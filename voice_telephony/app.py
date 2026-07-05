"""
Kisan Alert - Voice/Telephony Layer (Person 2) - Python version
-----------------------------------------------------------------
Handles:
  1. Incoming calls -> Hindi menu -> TTS advisory
  2. SMS advisory delivery (after diagnosis / advisory engine runs)

Env vars needed (put these in a .env file):
    TWILIO_ACCOUNT_SID
    TWILIO_AUTH_TOKEN
    TWILIO_FROM_NUMBER   (your Twilio trial number, e.g. +16592445481)
    ADVISORY_ENGINE_URL  (Person 3's backend URL, e.g. https://.../generate-advisory)

Optional env vars:
    PORT
    ADVISORY_TIMEOUT_SECONDS
    DEFAULT_CROP
    DEFAULT_LOCATION
"""

import json
import logging
import os
from urllib import error, request as urllib_request

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from twilio.rest import Client
from twilio.twiml.voice_response import Gather, VoiceResponse

load_dotenv()

app = Flask(__name__)

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("kisan-alert")

TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_FROM_NUMBER = os.environ.get("TWILIO_FROM_NUMBER")
ADVISORY_ENGINE_URL = os.environ.get("ADVISORY_ENGINE_URL")
ADVISORY_TIMEOUT_SECONDS = float(os.environ.get("ADVISORY_TIMEOUT_SECONDS", "5"))
DEFAULT_CROP = os.environ.get("DEFAULT_CROP", "wheat")
DEFAULT_LOCATION = os.environ.get("DEFAULT_LOCATION", "Unknown village")

client = None


@app.route("/", methods=["GET"])
def index():
    logger.info("Health check hit on /")
    return (
        "Kisan Alert voice service is running. Use /voice for Twilio webhooks "
        "or /send-advisory for SMS API calls.",
        200,
        {"Content-Type": "text/plain"},
    )


def get_mock_advisory(advisory_type):
    """Demo-safe fallback so the hackathon flow still works offline."""
    if advisory_type == "disease":
        return (
            "Aapki fasal mein blight rog paaya gaya hai. Turant fungicide "
            "spray karein aur khet mein paani ka jamaav na hone dein."
        )
    return (
        "Agle teen dinon mein baarish ki sambhavna hai. Sinchai abhi rok "
        "dein aur khaad ka chidkaav baarish ke baad karein."
    )


def build_advisory_payload(
    advisory_type,
    crop=None,
    diagnosis=None,
    location=None,
):
    """
    JSON contract for Person 3's advisory engine.

    When Person 3 shares the real endpoint, set ADVISORY_ENGINE_URL in .env and
    confirm whether their backend expects these exact field names:
      {
        "type": "disease" or "general",
        "crop": "wheat",
        "diagnosis": {...},   # optional dict
        "location": "..."     # optional string
      }

    If their JSON shape changes, this is the only helper you should need to edit.
    """
    payload = {
        "type": advisory_type,
        "crop": crop or DEFAULT_CROP,
        "diagnosis": diagnosis,
        "location": location or DEFAULT_LOCATION,
    }
    return payload


def fetch_advisory_text(
    advisory_type,
    crop=None,
    diagnosis=None,
    location=None,
):
    """
    Fetch advisory text from Person 3's backend with a safe fallback.

    Expected response JSON from Person 3:
      {
        "advisory_text": "Hindi advisory text here"
      }

    If their response uses another key later, update the parsing logic here.
    """
    fallback_text = get_mock_advisory(advisory_type)
    payload = build_advisory_payload(
        advisory_type=advisory_type,
        crop=crop,
        diagnosis=diagnosis,
        location=location,
    )

    if not ADVISORY_ENGINE_URL:
        logger.warning(
            "ADVISORY_ENGINE_URL is not set. Using mock advisory fallback for type=%s.",
            advisory_type,
        )
        return fallback_text

    body = json.dumps(payload).encode("utf-8")
    advisory_request = urllib_request.Request(
        ADVISORY_ENGINE_URL,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        logger.info(
            "Requesting advisory from engine url=%s type=%s crop=%s location=%s",
            ADVISORY_ENGINE_URL,
            payload["type"],
            payload["crop"],
            payload["location"],
        )
        with urllib_request.urlopen(
            advisory_request,
            timeout=ADVISORY_TIMEOUT_SECONDS,
        ) as response:
            raw_body = response.read().decode("utf-8")
            response_json = json.loads(raw_body)

        advisory_text = response_json.get("advisory_text")
        if not advisory_text:
            raise ValueError("Response missing advisory_text field")

        logger.info("Advisory engine call succeeded for type=%s", advisory_type)
        return advisory_text
    except (error.URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
        logger.exception(
            "Advisory engine failed. Falling back to mock advisory for type=%s. Error: %s",
            advisory_type,
            exc,
        )
        return fallback_text
    except Exception as exc:
        logger.exception(
            "Unexpected advisory engine error. Falling back to mock advisory for type=%s. Error: %s",
            advisory_type,
            exc,
        )
        return fallback_text


def get_twilio_client():
    """Create a Twilio client only when it is actually needed."""
    global client

    if client is None:
        if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
            raise RuntimeError(
                "TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN must be set to send SMS"
            )
        logger.info("Creating Twilio client")
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

    return client


def send_advisory_sms(to_number, message_body):
    """Helper to send an SMS via Twilio. Returns the Message resource."""
    if not TWILIO_FROM_NUMBER:
        raise RuntimeError("TWILIO_FROM_NUMBER must be set to send SMS")

    logger.info("Sending SMS to %s", to_number)
    message = get_twilio_client().messages.create(
        body=message_body,
        from_=TWILIO_FROM_NUMBER,
        to=to_number,
    )
    logger.info("SMS queued successfully sid=%s to=%s", message.sid, to_number)
    return message


@app.route("/voice", methods=["POST"])
def voice():
    logger.info("Incoming voice webhook from %s", request.form.get("From"))
    response = VoiceResponse()

    gather = Gather(num_digits=1, action="/menu", method="POST", timeout=6)
    gather.say(
        "Namaste, Kisan Alert mein aapka swagat hai. Fasal ki bimari ki "
        "jaankari ke liye ek dabayen. Mausam aur salaah ke liye do dabayen.",
        language="hi-IN",
        voice="Polly.Aditi",
    )
    response.append(gather)
    response.redirect("/voice")

    return str(response), 200, {"Content-Type": "text/xml"}


@app.route("/menu", methods=["POST"])
def menu():
    digit = request.form.get("Digits")
    caller_number = request.form.get("From")
    crop = request.form.get("crop") or DEFAULT_CROP
    location = request.form.get("location") or DEFAULT_LOCATION
    response = VoiceResponse()

    logger.info(
        "Menu selection received digit=%s from=%s crop=%s location=%s",
        digit,
        caller_number,
        crop,
        location,
    )

    if digit == "1":
        # Disease flow:
        # Replace the sample diagnosis below if Person 1/3 sends real diagnosis
        # data into this route later. The fetch helper already knows where to plug
        # Person 3's URL and how to parse advisory_text from the response.
        sample_diagnosis = {
            "disease": "blight",
            "confidence": 0.91,
            "remedy": "fungicide spray",
        }
        advisory_text = fetch_advisory_text(
            advisory_type="disease",
            crop=crop,
            diagnosis=sample_diagnosis,
            location=location,
        )

        response.say(advisory_text, language="hi-IN", voice="Polly.Aditi")
        response.say(
            "Yeh salaah aapko SMS mein bhi bheji ja rahi hai. Dhanyavaad.",
            language="hi-IN",
            voice="Polly.Aditi",
        )

        if caller_number:
            try:
                send_advisory_sms(caller_number, advisory_text)
            except Exception as exc:
                logger.exception("SMS send failed for disease flow: %s", exc)
        else:
            logger.warning("No caller number provided by Twilio for disease flow")

    elif digit == "2":
        advisory_text = fetch_advisory_text(
            advisory_type="general",
            crop=crop,
            diagnosis=None,
            location=location,
        )

        response.say(advisory_text, language="hi-IN", voice="Polly.Aditi")
        response.say(
            "Yeh salaah aapko SMS mein bhi bheji ja rahi hai. Dhanyavaad.",
            language="hi-IN",
            voice="Polly.Aditi",
        )

        if caller_number:
            try:
                send_advisory_sms(caller_number, advisory_text)
            except Exception as exc:
                logger.exception("SMS send failed for general flow: %s", exc)
        else:
            logger.warning("No caller number provided by Twilio for general flow")

    else:
        logger.warning("Invalid menu option received digit=%s from=%s", digit, caller_number)
        response.say(
            "Maaf kijiye, sahi option nahi mila.",
            language="hi-IN",
            voice="Polly.Aditi",
        )
        response.redirect("/voice")
        return str(response), 200, {"Content-Type": "text/xml"}

    response.hangup()
    return str(response), 200, {"Content-Type": "text/xml"}


@app.route("/send-advisory", methods=["POST"])
def send_advisory():
    """
    Endpoint Person 3 can call directly.

    Supported JSON body options:
      Option A: Send already-generated advisory text
        {
          "to": "+91XXXXXXXXXX",
          "advisory": "Ready-to-send Hindi text"
        }

      Option B: Let this service fetch the advisory text from Person 3's engine
        {
          "to": "+91XXXXXXXXXX",
          "type": "disease" or "general",
          "crop": "wheat",
          "diagnosis": {...},
          "location": "Village name"
        }

    Person 3 only needs to choose one of these flows.
    """
    data = request.get_json(force=True, silent=True) or {}
    logger.info("Received /send-advisory request keys=%s", sorted(data.keys()))

    to_number = data.get("to")
    advisory_text = data.get("advisory")
    advisory_type = data.get("type", "general")
    crop = data.get("crop") or DEFAULT_CROP
    diagnosis = data.get("diagnosis")
    location = data.get("location") or DEFAULT_LOCATION

    if not to_number:
        logger.warning("/send-advisory rejected because 'to' was missing")
        return jsonify({"error": "to field is required"}), 400

    if not advisory_text:
        advisory_text = fetch_advisory_text(
            advisory_type=advisory_type,
            crop=crop,
            diagnosis=diagnosis,
            location=location,
        )

    try:
        message = send_advisory_sms(to_number, advisory_text)
        return jsonify(
            {
                "status": "sent",
                "sid": message.sid,
                "advisory_text": advisory_text,
            }
        )
    except Exception as exc:
        logger.exception("Failed to send advisory SMS via /send-advisory: %s", exc)
        return jsonify({"error": str(exc)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    logger.info("Kisan Alert voice/SMS server running on port %s", port)
    logger.info("Expose this with: ngrok http %s", port)
    logger.info(
        "Then set your Twilio number's Voice webhook to: https://<ngrok-url>/voice"
    )
    app.run(host="0.0.0.0", port=port, debug=True)
