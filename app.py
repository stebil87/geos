from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

app = Flask(__name__)

# === CORS CONFIG ===
CORS(
    app,
    origins=["https://geos-services.ch"],
    supports_credentials=True,
    allow_headers=["Content-Type", "Authorization"],
    methods=["GET", "POST", "OPTIONS"]
)

# === ENV VARIABLES ===
MONGO_URI = os.environ.get(
    "MONGO_URI",
    "mongodb+srv://stebill87:Cquevino6+@geos.ylab820.mongodb.net/geos?retryWrites=true&w=majority&tls=true"
)

EMAIL_USER = os.environ.get("EMAIL_USER", "test@example.com")
EMAIL_PASS = os.environ.get("EMAIL_PASS", "")
EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.mailersend.net")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", 587))

# === DB CONNECTION ===
client = MongoClient(MONGO_URI)
db = client["geos"]
bookings = db["bookings"]

@app.route("/")
def home():
    return "✅ GEOS Backend is running!"

# === OPTIONS + BOOKING ===
@app.route("/submit-booking", methods=["POST", "OPTIONS"])
def submit_booking():
    if request.method == "OPTIONS":
        response = app.make_default_options_response()
        headers = response.headers
        headers["Access-Control-Allow-Origin"] = "https://geos-services.ch"
        headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
        headers["Access-Control-Allow-Methods"] = "POST,OPTIONS"
        headers["Access-Control-Allow-Credentials"] = "true"
        return response

    try:
        data = request.json
        data["submitted_at"] = datetime.utcnow()

        # Salva su MongoDB
        result = bookings.insert_one(data)

        # Invia email di conferma
        send_confirmation_email(data["email"], data)

        return jsonify({"status": "success", "id": str(result.inserted_id)})
    except Exception as e:
        print("❌ Errore nel backend:", str(e))
        return jsonify({"status": "error", "message": str(e)}), 500

# === EMAIL FUNCTION ===
def send_confirmation_email(to_email, data):
    subject = "Conferma richiesta – GEOS Services Ltd."
    body = f"""
Grazie per la sua richiesta, che abbiamo ricevuto.

📝 Riepilogo della prenotazione:
Nome: {data.get('firstname')} {data.get('lastname')}
Nazionalità: {data.get('nationality')}
Data di nascita: {data.get('birthdate')}
Email: {data.get('email')}
Telefono: {data.get('phone')}
Residenza: {data.get('residence')}
Partenza: {data.get('pickup_address')}
Destinazione: {data.get('dropoff_address')}
Data e ora: {data.get('datetime')}
Richieste particolari: {data.get('notes', '-')}

Sarete ricontattati entro 24 ore per una conferma.

Cordiali saluti,
GEOS Services Ltd.
"""

    msg = MIMEMultipart()
    msg['From'] = EMAIL_USER
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.send_message(msg)
        server.quit()
        print("✅ Email inviata.")
    except Exception as e:
        print("❌ Errore nell'invio email:", e)
        raise

# === CORS HEADERS POST-RESPONSE ===
@app.after_request
def after_request(response):
    response.headers["Access-Control-Allow-Origin"] = "https://geos-services.ch"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    return response

# === ENTRYPOINT ===
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
