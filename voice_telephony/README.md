# Voice Telephony Layer

This module contains the Twilio + Flask voice and SMS delivery layer for Kisan Alert.

## What it does

- Handles incoming Twilio calls on `/voice`
- Plays a Hindi IVR menu and routes to `/menu`
- Fetches advisory text from Person 3's backend using `ADVISORY_ENGINE_URL`
- Falls back to mock advisories if the backend is down or slow
- Sends advisory text over SMS using Twilio
- Exposes `/send-advisory` so the backend can trigger SMS delivery directly

## Setup

```powershell
py -3.14 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Fill in `.env` with your Twilio values and Person 3's advisory endpoint URL.

## Run

```powershell
python app.py
```

## Test

```powershell
python test_integration.py
```

The integration test uses Flask's test client and stubs SMS sending, so it does not require a live Twilio call.
