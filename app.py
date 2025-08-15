import os
import json
import datetime
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash

# ------------ Configuration ------------
# LOCAL SAVE (default True): Save to user's Desktop/Registration & Desktop/Missing
# For Render (cloud), set environment variable LOCAL_SAVE=0
USE_LOCAL_SAVE = os.environ.get("LOCAL_SAVE", "1") == "1"

if USE_LOCAL_SAVE:
    BASE_DIR = Path.home() / "Desktop"
else:
    BASE_DIR = Path(__file__).parent.resolve()  # cloud-safe

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
TWILIO_WHATSAPP_FROM = os.environ.get("TWILIO_WHATSAPP_FROM", "")  # e.g. "whatsapp:+14155238886"

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret")  # flash messages

ALLOWED_EXT = {".jpg", ".jpeg", ".png"}


# ------------ Helpers ------------
def is_allowed(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_EXT

def next_index(folder: Path, prefix: str) -> int:
    """
    Return next integer index for files like prefix + <n>.ext
    e.g., p1.jpg, p2.jpg ... → returns max(n)+1
    """
    max_i = 0
    if folder.exists():
        for p in folder.iterdir():
            if p.is_file() and p.stem.startswith(prefix):
                # extract number from stem after prefix
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

def send_whatsapp_message(to_number: str, text: str):
    """
    Sends WhatsApp message via Twilio if credentials present.
    to_number: in E.164 with whatsapp:, e.g. 'whatsapp:+91XXXXXXXXXX'
    """
    if not (TWILIO_SID and TWILIO_TOKEN and TWILIO_WHATSAPP_FROM):
        return False, "Twilio not configured"
    try:
        from twilio.rest import Client
        client = Client(TWILIO_SID, TWILIO_TOKEN)
        msg = client.messages.create(
            from_=TWILIO_WHATSAPP_FROM,
            to=f"whatsapp:{to_number.replace('whatsapp:', '')}" if not to_number.startswith("whatsapp:") else to_number,
            body=text
        )
        return True, msg.sid
    except Exception as e:
        return False, str(e)


# ------------ Routes ------------
@app.route("/", methods=["GET"])
def index():
    # Registration page
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

        # Folder structure: Registration/<phone>/family/
        user_root = REG_ROOT / phone
        family_folder = user_root / "family"
        family_folder.mkdir(parents=True, exist_ok=True)

        # Dynamic family photos
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

        # WhatsApp confirmation (optional)
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

        # Folder: Missing/<phone>/
        user_miss = MISS_ROOT / phone
        user_miss.mkdir(parents=True, exist_ok=True)

        # Save missing photo as m<index>.ext
        idx = next_index(user_miss, "m")
        ext = Path(mphoto.filename).suffix.lower()
        photo_path = user_miss / f"m{idx}{ext}"
        mphoto.save(photo_path)

        # Save description alongside as m<index>.txt
        if desc:
            (user_miss / f"m{idx}.txt").write_text(desc, encoding="utf-8")

        # Notification entry
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        notification = {
            "phone": phone,
            "file": photo_path.name,
            "timestamp": ts,
            "status": "reported",
            "description": desc[:140]  # short preview
        }
        save_notifications(notification)

        # WhatsApp acknowledgement (optional)
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
    # latest first
    data = list(reversed(data))
    return jsonify(data)

# -------------- Run --------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    # Important for Render: host=0.0.0.0 and PORT from env
    app.run(host="0.0.0.0", port=port, debug=True)
