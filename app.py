from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, jsonify, make_response
)
from pathlib import Path
from datetime import datetime
import os, json, secrets

# ---------- App ----------
app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = os.getenv("FLASK_SECRET_KEY", secrets.token_hex(16))

# ---------- Storage ----------
BASE = Path(".")
REG_DIR = BASE / "Registration"
MIS_DIR = BASE / "Missing"
REG_DIR.mkdir(exist_ok=True)
MIS_DIR.mkdir(exist_ok=True)

NOTIF_FILE = BASE / "notifications.json"
if not NOTIF_FILE.exists():
    NOTIF_FILE.write_text("[]", encoding="utf-8")

# ---------- i18n ----------
INDIAN_LANGUAGES = [
    {"code": "en", "name": "English"},
    {"code": "hi", "name": "Hindi"},
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

# ---------- WhatsApp (optional via Twilio) ----------
USE_TWILIO = bool(os.getenv("TWILIO_ACCOUNT_SID") and os.getenv("TWILIO_AUTH_TOKEN") and os.getenv("TWILIO_WHATSAPP_FROM"))
if USE_TWILIO:
    from twilio.rest import Client
    twilio_client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
    WHATSAPP_FROM = f"whatsapp:{os.getenv('TWILIO_WHATSAPP_FROM')}"  # e.g. whatsapp:+14155238886

def send_whatsapp(to_e164, message):
    """Safe WhatsApp sender (no crash if Twilio not set)."""
    if not USE_TWILIO:
        return False, "Twilio disabled"
    try:
        twilio_client.messages.create(
            from_=WHATSAPP_FROM,
            to=f"whatsapp:{to_e164}",
            body=message
        )
        return True, "sent"
    except Exception as e:
        return False, str(e)

# ---------- Helpers ----------
def save_photos(files, folder: Path, prefix: str = "p"):
    folder.mkdir(parents=True, exist_ok=True)
    idx = 1
    for f in files:
        if not f or not f.filename:
            continue
        ext = os.path.splitext(f.filename)[1].lower() or ".jpeg"
        path = folder / f"{prefix}{idx}{ext}"
        f.save(path)
        idx += 1
    return idx - 1

def append_notification(kind, phone, extra=None):
    try:
        data = json.loads(NOTIF_FILE.read_text(encoding="utf-8"))
    except Exception:
        data = []
    item = {
        "ts": datetime.utcnow().isoformat() + "Z",
        "kind": kind,                 # "registration" | "missing"
        "phone": phone,
        "extra": extra or {}
    }
    data.append(item)
    NOTIF_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

# ---------- Routes ----------
@app.route("/language", methods=["GET", "POST"])
def language():
    if request.method == "GET":
        return render_template("language.html", languages=INDIAN_LANGUAGES)
    lang = request.form.get("lang") or request.args.get("lang") or "en"
    resp = make_response(redirect(url_for("index")))
    # keep for one year
    resp.set_cookie("lang", lang, max_age=60*60*24*365)
    return resp

@app.route("/")
def index():
    # Main registration form
    lang = request.cookies.get("lang", "en")
    return render_template("index.html", lang=lang)

@app.route("/register", methods=["POST"])
def register():
    phone = (request.form.get("mobile_no") or "").strip()
    whatsapp = (request.form.get("whatsapp_no") or "").strip()
    secondary = (request.form.get("secondary_no") or "").strip()

    if not phone or not whatsapp:
        flash("Mobile and WhatsApp numbers are required.")
        return redirect(url_for("index"))

    folder = REG_DIR / phone
    count = save_photos(request.files.getlist("reg_photos[]"), folder, prefix="p")

    append_notification("registration", phone, {"photos": count})
    # WhatsApp confirmation with reopen link
    portal_link = request.url_root.rstrip("/")  # home as portal link
    msg = f"✅ Registration completed.\nPhone: {phone}\nPhotos: {count}\nOpen portal: {portal_link}"
    send_whatsapp(whatsapp, msg)

    flash("Registration submitted successfully.")
    return redirect(url_for("index"))

@app.route("/report")
def report_page():
    lang = request.cookies.get("lang", "en")
    return render_template("report.html", lang=lang)

@app.route("/report_missing", methods=["POST"])
def report_missing():
    phone = (request.form.get("reporter_phone") or "").strip()
    whatsapp = (request.form.get("reporter_whatsapp") or "").strip()
    desc = (request.form.get("description") or "").strip()

    if not phone or not whatsapp:
        flash("Reporter Phone and WhatsApp are required.")
        return redirect(url_for("report_page"))

    folder = MIS_DIR / phone
    photos = request.files.getlist("missing_photos[]")
    count = save_photos(photos, folder, prefix="p")

    if desc:
        # we keep a single m1.txt for simplicity; can be versioned if you want
        (folder / "m1.txt").write_text(desc, encoding="utf-8")

    append_notification("missing", phone, {"photos": count, "has_desc": bool(desc)})

    msg = f"📣 Missing person report received.\nReporter: {phone}\nPhotos: {count}\nWe’ll notify you of updates."
    send_whatsapp(whatsapp, msg)

    flash("Missing person report submitted.")
    return redirect(url_for("report_page"))

@app.route("/notifications")
def notifications_page():
    return render_template("notifications.html")

@app.route("/api/notifications")
def notifications_api():
    try:
        data = json.loads(NOTIF_FILE.read_text(encoding="utf-8"))
    except Exception:
        data = []
    # newest first
    data = list(reversed(data))
    return jsonify(data)

# ---------- Run ----------
if __name__ == "__main__":
    app.run(debug=True)
