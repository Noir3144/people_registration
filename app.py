import os
import json
import datetime
import re
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash

# ------------ Configuration ------------
USE_LOCAL_SAVE = os.environ.get("LOCAL_SAVE", "1") == "1"

if USE_LOCAL_SAVE:
    BASE_DIR = Path.home() / "Desktop"
else:
    BASE_DIR = Path(__file__).parent.resolve()

REG_ROOT = BASE_DIR / "Registration"
MISS_ROOT = BASE_DIR / "Missing"
REG_ROOT.mkdir(parents=True, exist_ok=True)
MISS_ROOT.mkdir(parents=True, exist_ok=True)

NOTIF_FILE = MISS_ROOT / "notifications.json"
if not NOTIF_FILE.exists():
    NOTIF_FILE.write_text("[]", encoding="utf-8")

# Twilio WhatsApp (optional)
TWILIO_SID = os.environ.get("TWILIO_ACCOUNT_SID", "")
TWILIO_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_FROM = os.environ.get("TWILIO_WHATSAPP_FROM", "")
DIAG_KEY = os.environ.get("DIAG_KEY", "MyTest123")

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret")

ALLOWED_EXT = {".jpg", ".jpeg", ".png"}

# ------------ Helpers ------------
def is_allowed(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_EXT

def next_index(folder: Path, prefix: str) -> int:
    max_i = 0
    if folder.exists():
        for p in folder.iterdir():
            if p.is_file() and p.stem.startswith(prefix):
                num_part = p.stem[len(prefix):]
                if num_part.isdigit():
                    max_i = max(max_i, int(num_part))
    return max_i + 1

def save_notifications(entry: dict):
    try:
        data = json.loads(NOTIF_FILE.read_text(encoding="utf-8"))
    except Exception:
        data = []
    data.append(entry)
    NOTIF_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def normalize_e164(num: str) -> str:
    num = (num or "").strip()
    num = re.sub(r"[^\d+]", "", num)
    if not num.startswith("+"):
        if num.startswith("0"):
            num = num.lstrip("0")
        num = "+91" + num
    return num

def send_whatsapp_message(to_number: str, text: str):
    if not (TWILIO_SID and TWILIO_TOKEN and TWILIO_WHATSAPP_FROM):
        print("[TWILIO] Missing credentials")
        return False, "Twilio not configured"
    try:
        from twilio.rest import Client
        client = Client(TWILIO_SID, TWILIO_TOKEN)
        to = normalize_e164(to_number)
        msg = client.messages.create(
            from_=TWILIO_WHATSAPP_FROM,
            to=f"whatsapp:{to}",
            body=text
        )
        print("[TWILIO] Sent:", msg.sid)
        return True, msg.sid
    except Exception as e:
        print("[TWILIO] Error:", e)
        return False, str(e)

# ------------ Routes ------------
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/report", methods=["GET"])
def report_missing_page():
    return render_template("report.html")

@app.route("/register", methods=["POST"])
def register():
    try:
        phone = (request.form.get("phone") or "").strip()
        whatsapp = (request.form.get("whatsapp") or "").strip()
        if not phone or not whatsapp:
            flash("Phone aur WhatsApp number required hai.")
            return redirect(url_for("index"))

        user_root = REG_ROOT / phone
        family_folder = user_root / "family"
        family_folder.mkdir(parents=True, exist_ok=True)

        photos = request.files.getlist("family_photos")
        saved_count = 0
        for f in photos:
            if not f or not f.filename:
                continue
            if not is_allowed(f.filename):
                continue
            idx = next_index(family_folder, "p")
            ext = Path(f.filename).suffix.lower()
            save_path = family_folder / f"p{idx}{ext}"
            f.save(save_path)
            saved_count += 1

        site_url = request.host_url.rstrip("/")
        message = (
            f"Registration successful for {phone}.\n"
            f"Photos saved: {saved_count}.\n"
            f"Reopen the portal anytime: {site_url}"
        )
        if whatsapp:
            send_whatsapp_message(whatsapp, message)

        flash("Registration successful.")
        return redirect(url_for("index"))
    except Exception as e:
        flash(f"Upload error: {e}")
        return redirect(url_for("index"))

@app.route("/submit-missing", methods=["POST"])
def submit_missing():
    try:
        phone = (request.form.get("phone") or "").strip()
        whatsapp = (request.form.get("whatsapp") or "").strip()
        desc = (request.form.get("description") or "").strip()
        mphoto = request.files.get("missing_photo")

        if not phone or not whatsapp or not mphoto or not mphoto.filename:
            flash("Phone, WhatsApp aur Missing photo required hai.")
            return redirect(url_for("report_missing_page"))

        if not is_allowed(mphoto.filename):
            flash("Missing photo sirf JPG/JPEG/PNG allowed hai.")
            return redirect(url_for("report_missing_page"))

        user_miss = MISS_ROOT / phone
        user_miss.mkdir(parents=True, exist_ok=True)

        idx = next_index(user_miss, "m")
        ext = Path(mphoto.filename).suffix.lower()
        photo_path = user_miss / f"m{idx}{ext}"
        mphoto.save(photo_path)

        if desc:
            (user_miss / f"m{idx}.txt").write_text(desc, encoding="utf-8")

        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        notification = {
            "phone": phone,
            "file": photo_path.name,
            "timestamp": ts,
            "status": "reported",
            "description": desc[:140]
        }
        save_notifications(notification)

        site_url = request.host_url.rstrip("/")
        msg = (
            f"Missing report received for {phone} at {ts}.\n"
            f"We will notify here if found.\n"
            f"Portal: {site_url}"
        )
        if whatsapp:
            send_whatsapp_message(whatsapp, msg)

        flash("Missing report submitted.")
        return redirect(url_for("report_missing_page"))
    except Exception as e:
        flash(f"Missing report error: {e}")
        return redirect(url_for("report_missing_page"))

@app.route("/notifications", methods=["GET"])
def notifications():
    try:
        data = json.loads(NOTIF_FILE.read_text(encoding="utf-8"))
    except Exception:
        data = []
    data = list(reversed(data))
    return jsonify(data)

@app.route("/diag/twilio")
def diag_twilio():
    key = request.args.get("key", "")
    if key != DIAG_KEY:
        return {"ok": False, "error": "unauthorized"}, 401

    to = request.args.get("to", "")
    if not to:
        return {"ok": False, "error": "missing to"}, 400

    ok, info = send_whatsapp_message(to, "[Test] Render WhatsApp Test OK")
    return {"ok": ok, "info": info}

# -------------- Run --------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
