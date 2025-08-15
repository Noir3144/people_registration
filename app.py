import os
import json
import datetime
import re
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash

# ---------------- Configuration ----------------
# LOCAL_SAVE=1 (default) -> save to ~/Desktop on your laptop (as requested)
# LOCAL_SAVE=0 -> save alongside app (for Render)
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

ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp"}

# ---------------- Helpers ----------------
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

def normalize_e164(num: str) -> str:
    """Return number in proper E.164 format (default +91)."""
    num = (num or "").strip()
    num = re.sub(r"[^\d+]", "", num)
    if not num.startswith("+"):
        if num.startswith("0"):
            num = num.lstrip("0")
        num = "+91" + num
    return num

def save_notifications(entry: dict):
    try:
        data = json.loads(NOTIF_FILE.read_text(encoding="utf-8"))
    except Exception:
        data = []
    data.append(entry)
    NOTIF_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def send_whatsapp_message(to_number: str, text: str):
    """Send WhatsApp message via Twilio (optional)."""
    if not (TWILIO_SID and TWILIO_TOKEN and TWILIO_WHATSAPP_FROM):
        print("[TWILIO] Skipped: credentials missing")
        return False, "Twilio not configured"
    try:
        from twilio.rest import Client
        client = Client(TWILIO_SID, TWILIO_TOKEN)
        to = normalize_e164(to_number)
        if not to.startswith("whatsapp:"):
            to = f"whatsapp:{to}"
        from_num = TWILIO_WHATSAPP_FROM
        if not from_num.startswith("whatsapp:"):
            from_num = f"whatsapp:{from_num}"
        msg = client.messages.create(from_=from_num, to=to, body=text)
        print("[TWILIO] Sent:", msg.sid)
        return True, msg.sid
    except Exception as e:
        print("[TWILIO] Error:", e)
        return False, str(e)

# ---------------- Routes ----------------
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/report", methods=["GET"])
def report_missing_page():
    return render_template("report.html")

@app.route("/notifications-board", methods=["GET"])
def notifications_board():
    return render_template("notifications.html")

@app.route("/notifications", methods=["GET"])
def notifications():
    try:
        data = json.loads(NOTIF_FILE.read_text(encoding="utf-8"))
    except Exception:
        data = []
    data = list(reversed(data))
    return jsonify(data)

@app.route("/register", methods=["POST"])
def register():
    try:
        phone = (request.form.get("phone") or "").strip()
        whatsapp = (request.form.get("whatsapp") or "").strip()
        secondary = (request.form.get("secondary") or "").strip()

        if not phone or not whatsapp:
            flash("msg.phone_whatsapp_required")
            return redirect(url_for("index"))

        user_root = REG_ROOT / phone
        user_root.mkdir(parents=True, exist_ok=True)

        # Unlimited dynamic slots: collect all inputs named 'family_photos'
        photos = request.files.getlist("family_photos")
        saved_count = 0
        for f in photos:
            if not f or not f.filename:
                continue
            if not is_allowed(f.filename):
                continue
            idx = next_index(user_root, "p")
            ext = Path(f.filename).suffix.lower()
            save_path = user_root / f"p{idx}{ext}"
            f.save(save_path)
            saved_count += 1

        site_url = request.host_url.rstrip("/")
        message = (
            f"Registration successful for {phone}.\n"
            f"Photos saved: {saved_count}.\n"
            f"Portal: {site_url}"
        )
        if whatsapp:
            send_whatsapp_message(whatsapp, message)

        # For front-end i18n, flash the key; the page maps key -> text.
        flash("msg.registration_success")
        return redirect(url_for("index"))
    except Exception as e:
        print("Register error:", e)
        flash("msg.upload_error")
        return redirect(url_for("index"))

@app.route("/submit-missing", methods=["POST"])
def submit_missing():
    try:
        phone = (request.form.get("phone") or "").strip()
        whatsapp = (request.form.get("whatsapp") or "").strip()
        desc = (request.form.get("description") or "").strip()

        if not phone or not whatsapp:
            flash("msg.phone_whatsapp_required")
            return redirect(url_for("report_missing_page"))

        user_miss = MISS_ROOT / phone
        user_miss.mkdir(parents=True, exist_ok=True)

        # Support unlimited photos: 'missing_photos'
        mphotos = request.files.getlist("missing_photos")
        any_saved = False

        for f in mphotos:
            if not f or not f.filename:
                continue
            if not is_allowed(f.filename):
                continue
            idx = next_index(user_miss, "m")
            ext = Path(f.filename).suffix.lower()
            photo_path = user_miss / f"m{idx}{ext}"
            f.save(photo_path)
            any_saved = True
            if desc:
                (user_miss / f"m{idx}.txt").write_text(desc, encoding="utf-8")

            ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            notification = {
                "phone": phone,
                "file": photo_path.name,
                "timestamp": ts,
                "status": "reported",
                "description": (desc or "")[:140]
            }
            save_notifications(notification)

        if not any_saved:
            flash("msg.missing_photo_required")
            return redirect(url_for("report_missing_page"))

        site_url = request.host_url.rstrip("/")
        msg = (
            f"Missing report received for {phone}.\n"
            f"We will notify here if found.\n"
            f"Portal: {site_url}"
        )
        if whatsapp:
            send_whatsapp_message(whatsapp, msg)

        flash("msg.missing_report_success")
        return redirect(url_for("report_missing_page"))
    except Exception as e:
        print("Missing report error:", e)
        flash("msg.missing_report_error")
        return redirect(url_for("report_missing_page"))

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

@app.route("/healthz")
def healthz():
    return {"ok": True}

# ---------------- Run ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
