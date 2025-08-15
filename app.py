from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, make_response
from pathlib import Path
import os
import json

app = Flask(__name__)
app.secret_key = "replace_with_a_secret_key"

# Ensure required folders exist
os.makedirs("Registration", exist_ok=True)
os.makedirs("Missing", exist_ok=True)

# Ensure notifications file exists
NOTIF_FILE = Path("notifications.json")
if not NOTIF_FILE.exists():
    NOTIF_FILE.write_text("[]", encoding="utf-8")

# Languages list
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

@app.route("/language", methods=["GET", "POST"])
def language():
    if request.method == "GET":
        return render_template("language.html", languages=INDIAN_LANGUAGES)
    lang = request.form.get("lang", "en")
    resp = make_response(redirect(url_for("index")))
    resp.set_cookie("lang", lang, max_age=60*60*24*365)
    return resp

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["POST"])
def register():
    phone = request.form.get("mobile_no")
    whatsapp = request.form.get("whatsapp_no")

    if not phone or not whatsapp:
        flash("Mobile and WhatsApp number are required.")
        return redirect(url_for("index"))

    reg_folder = os.path.join("Registration", phone)
    os.makedirs(reg_folder, exist_ok=True)

    if "family_photos" in request.files:
        files = request.files.getlist("family_photos")
        for idx, file in enumerate(files, start=1):
            if file.filename:
                ext = os.path.splitext(file.filename)[1] or ".jpeg"
                file.save(os.path.join(reg_folder, f"p{idx}{ext}"))

    flash("Registration successful!")
    return redirect(url_for("index"))

@app.route("/report", methods=["GET"])
def report_page():
    lang = request.cookies.get("lang", "en")
    return render_template("report.html", lang=lang)

@app.route("/report_missing", methods=["POST"])
def report_missing():
    phone = request.form.get("reporter_phone")
    whatsapp = request.form.get("reporter_whatsapp")
    description = request.form.get("description", "")

    if not phone or not whatsapp:
        flash("Reporter phone and WhatsApp number are required.")
        return redirect(url_for("report_page"))

    miss_folder = os.path.join("Missing", phone)
    os.makedirs(miss_folder, exist_ok=True)

    if "missing_photos" in request.files:
        files = request.files.getlist("missing_photos")
        for idx, file in enumerate(files, start=1):
            if file.filename:
                ext = os.path.splitext(file.filename)[1] or ".jpeg"
                file.save(os.path.join(miss_folder, f"p{idx}{ext}"))

    if description:
        with open(os.path.join(miss_folder, f"m1.txt"), "w", encoding="utf-8") as f:
            f.write(description)

    flash("Missing person report submitted!")
    return redirect(url_for("report_page"))

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

if __name__ == "__main__":
    app.run(debug=True)
