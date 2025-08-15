import os
import json
import datetime
import re
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, make_response

# ------------ Configuration ------------
USE_LOCAL_SAVE = os.environ.get("LOCAL_SAVE", "1") == "1"

if USE_LOCAL_SAVE:
    # Default to Desktop to make it obvious for local testing. Change as needed.
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
    """Return number in E.164-like format (with +91 if missing)."""
    num = (num or "").strip()
    num = re.sub(r"[^\d+]", "", num)
    if not num:
        return num
    if not num.startswith("+"):
        if num.startswith("0"):
            num = num.lstrip("0")
        num = "+91" + num
    return num

def send_whatsapp_message(to_number: str, text: str):
    """Send WhatsApp message via Twilio (optional)."""
    if not (TWILIO_SID and TWILIO_TOKEN and TWILIO_WHATSAPP_FROM):
        print("[TWILIO] Missing credentials (skipping)")
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
        msg = client.messages.create(
            from_=from_num,
            to=to,
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
    # read chosen language from cookie (used by frontend JS)
    lang = request.cookies.get("lang", "en")
    return render_template("index.html", lang=lang)

@app.route("/register", methods=["POST"])
def register():
    try:
        phone = (request.form.get("phone") or "").strip()
        whatsapp = (request.form.get("whatsapp") or "").strip()
        secondary = (request.form.get("secondary") or "").strip()

        if not phone or not whatsapp:
            flash("Phone and WhatsApp number are required.")
            return redirect(url_for("index"))

        # Save registration folder and family photos
        user_root = REG_ROOT / phone
        user_root.mkdir(parents=True, exist_ok=True)

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

        # Save a small metadata file for contact numbers
        meta = {
            "phone": phone,
            "whatsapp": whatsapp,
            "secondary": secondary,
            "timestamp": datetime.datetime.now().isoformat()
        }
        (user_root / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

        site_url = request.host_url.rstrip("/")
        message = (
            f"Registration successful for {phone}.\n"
            f"Photos saved: {saved_count}.\n"
            f"Portal: {site_url}"
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
        # support multiple uploaded files from missing form
        photos = request.files.getlist("missing_photos")

        if not phone or not whatsapp or not photos or all((not p or not p.filename) for p in photos):
            flash("Phone, WhatsApp and at least one photo are required.")
            return redirect(url_for("report_missing_page"))

        user_miss = MISS_ROOT / phone
        user_miss.mkdir(parents=True, exist_ok=True)

        saved = 0
        for p in photos:
            if not p or not p.filename:
                continue
            if not is_allowed(p.filename):
                continue
            idx = next_index(user_miss, "m")
            ext = Path(p.filename).suffix.lower()
            photo_path = user_miss / f"m{idx}{ext}"
            p.save(photo_path)
            # create a description file per photo (if provided)
            if desc:
                (user_miss / f"m{idx}.txt").write_text(desc, encoding="utf-8")
            saved += 1

            ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            notification = {
                "phone": phone,
                "file": photo_path.name,
                "timestamp": ts,
                "status": "reported",
                "description": (desc[:200] if desc else "")
            }
            save_notifications(notification)

        site_url = request.host_url.rstrip("/")
        msg = (
            f"Missing report received for {phone} at {datetime.datetime.now().isoformat()}.\n"
            f"Photos saved: {saved}.\n"
            f"Portal: {site_url}"
        )
        if whatsapp:
            send_whatsapp_message(whatsapp, msg)

        flash("Missing report submitted.")
        return redirect(url_for("report_missing_page"))
    except Exception as e:
        flash(f"Missing report error: {e}")
        return redirect(url_for("report_missing_page"))

@app.route("/diag/twilio")
def diag_twilio():
    key = request.args.get("key", "")
    if key != DIAG_KEY:
        return {"ok": False, "error": "unauthorized"}, 401

    to = request.args.get("to", "")
    if not to:
        return {"ok": False, "error": "missing to"}, 400

    ok, info = send_whatsapp_message(to, "[Test] Portal WhatsApp Test")
    return {"ok": ok, "info": info}

# -------------- Run --------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

@app.route("/language", methods=["GET", "POST"])
def language():
    INDIAN_LANGUAGES = [
        {"code": "hi", "name": "Hindi"},
        {"code": "en", "name": "English"},
        {"code": "bn", "name": "Bengali"},
        {"code": "ta", "name": "Tamil"},
        {"code": "te", "name": "Telugu"},
        {"code": "ml", "name": "Malayalam"},
        {"code": "gu", "name": "Gujarati"},
        {"code": "mr", "name": "Marathi"},
        {"code": "kn", "name": "Kannada"},
        {"code": "pa", "name": "Punjabi"},
        {"code": "ur", "name": "Urdu"},
    ]
    if request.method == "GET":
        return render_template("language.html", languages=INDIAN_LANGUAGES)
    lang = request.form.get("lang", "en")
    resp = make_response(redirect(url_for("index")))
    resp.set_cookie("lang", lang, max_age=60*60*24*365)
    return resp


@app.route("/report", methods=["GET"])
def report_missing_page():
    lang = request.cookies.get("lang", "en")
    return render_template("report.html", lang=lang)


@app.route("/notifications", methods=["GET"])
def notifications():
    try:
        data = json.loads(NOTIF_FILE.read_text(encoding="utf-8"))
    except Exception:
        data = []
    data = list(reversed(data))

    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        return jsonify(data)

    return render_template("notifications.html", notifications=data)
