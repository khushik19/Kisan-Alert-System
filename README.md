# Kisan Alert — AI Voice & SMS Crop Advisory System
### Track 4 | Build with AI: Code for Communities (Indore Edition)
**Team: Cosmos**

Kisan Alert is an end-to-end, resilient plant disease diagnostic and localized agricultural advisory system designed for low-connectivity, non-smartphone farmers in rural India. By offering voice-call IVR menus and SMS callback channels in native Hindi, Kisan Alert breaks the digital divide to reduce crop loss and input waste.

---

## 🏗️ Project Architecture

The system is composed of four main interoperable modules:

```
      [Input Channels]                              [AI Brain]                            [Delivery & Visuals]

 📱 Flutter Mobile App (Camera) ──┐
                                  ├──→ ⚙️ FastAPI Advisory Engine ──→ [Gemini 2.5-Flash (Vision & Text)]
 🌾 Streamlit Sandbox (Upload)  ──┘         (Weather + Crop Stage)                  │
                                                      │                              │
                                                      ▼                              ▼
 📞 Telephone Call (IVR Menu)   ──→ 📞 Twilio / Voice Server (Flask) ──────→ SMS / Voice TTS Output
                                                      │
                                                      ▼
 📊 Streamlit Live Dashboard    ←───────────────── GET /queries
```

1. **AI Advisory Engine (Backend):** Orchestrates disease diagnostics using **Gemini 2.5-Flash** (with automatic model fallback to `gemini-2.0-flash` & `gemini-2.0-flash-lite` on quota exhaustion). Integrates real-time meteorology data for Indore (OpenWeatherMap) and crop growth assumptions to produce weather-aware advisories (e.g. warning the farmer not to spray fungicides if rain is expected).
2. **Outbound Voice & SMS Layer (Telephony):** A Flask service integrating Twilio's Programmable Voice and Messaging API. Handles Hindi IVR menus and dispatches Hindi advisories.
3. **Live Advisory Dashboard (Web):** A Streamlit interface displaying real-time scores, diagnostic reports, and SMS queues. Features a live drag-and-drop crop diagnosis sandbox.
4. **Kisan Mobile App (Mobile):** A Flutter app compiling natively for Android, Web, and Desktop, enabling field agents or kiosk staff to diagnose crops on-the-spot.

---

## 📢 Critical Notice on Twilio Trial Accounts (Demo Limitations)

Because this prototype operates on a **Twilio Trial Account**, telecom anti-spam rules apply:
- **Verified Caller ID Requirement:** SMS and Voice alerts **can only be delivered to numbers that are pre-verified in the Twilio Console** (like the developer's phone number).
- **If you test with an unverified phone number:** Twilio will reject the delivery and the server logs will return a `400 Bad Request` warning.
- **Single Source of Truth (The Dashboard):** To prove end-to-end execution without registering every number, judges can refer to the **Streamlit Dashboard's "Outbound Advisory Status" tab**. It intercepts, logs, and displays the outbound SMS advisory text in real-time, matching exactly what leaves the backend.

---

## 🚀 Setup & Local Execution Guide

### Prerequisites
- Python 3.10+
- Node.js (for exposing endpoints via localtunnel)
- Flutter SDK (optional, only to compile/run the mobile client)

---

### Step 1: Clone and Configure Environment

Create a `.env` file in **`backend/`** folder:
```env
OPENWEATHER_API_KEY=your_openweathermap_api_key
GEMINI_API_KEY=your_gemini_api_key
DEMO_LAT=22.7196
DEMO_LON=75.8577
DEMO_CROP=rice
```

Create a `.env` file in **`voice_telephony/`** folder:
```env
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_FROM_NUMBER=your_twilio_virtual_phone_number
ADVISORY_ENGINE_URL=https://wide-sites-bet.loca.lt/advisory
ADVISORY_TIMEOUT_SECONDS=10
DEFAULT_CROP=rice
DEFAULT_LOCATION=Indore
PORT=3000
```

---

### Step 2: Start the FastAPI Backend

1. Navigate to the `backend` folder:
   ```bash
   cd backend
   ```
2. Initialize and activate the virtual environment:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate      # Windows Powershell
   # OR source venv/bin/activate (Linux/Mac)
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install pillow python-multipart
   ```
4. Start the server on port 8000:
   ```bash
   python -m uvicorn main:app --port 8000
   ```

---

### Step 3: Expose the Backend Publicly (localtunnel)

For the dashboard and mobile app to connect, expose port 8000 with localtunnel using our configured subdomain:
```bash
npx -y localtunnel --port 8000 --subdomain wide-sites-bet
```
*Note: This creates the public endpoint `https://wide-sites-bet.loca.lt/` used by other services.*

---

### Step 4: Start the Telephony Voice Server

1. Open a new terminal and navigate to `voice_telephony`:
   ```bash
   cd voice_telephony
   ```
2. Activate your virtual environment and start the Flask app:
   ```bash
   ..\backend\venv\Scripts\python.exe app.py
   ```
   *Note: Exposing port 3000 (Flask) to Twilio webhooks is only needed if you want to test incoming voice phone calls.*

---

### Step 5: Run the Streamlit Dashboard

1. Open a new terminal and navigate to `dashboard`:
   ```bash
   cd dashboard
   ```
2. Install Streamlit (if not installed) and start the dashboard on port 8501:
   ```bash
   ..\backend\venv\Scripts\pip.exe install streamlit pandas
   ..\backend\venv\Scripts\python.exe -m streamlit run app.py --server.port 8501
   ```
3. Visit **`http://localhost:8501`** in your browser. The sidebar should display **`API Status: Connected 🟢`** automatically bypassing the localtunnel warning.

---

### Step 6: Launch the Mobile Client (Optional)

1. Navigate to `mobile_app`:
   ```bash
   cd mobile_app
   ```
2. Download Flutter packages:
   ```bash
   flutter pub get
   ```
3. Launch the application on Chrome:
   ```bash
   flutter run -d chrome
   ```
   *Note: If testing on Windows desktop via `flutter run -d windows`, make sure to select "Choose from Gallery" (as Windows does not support camera capture via the standard ImagePicker plugin).*
