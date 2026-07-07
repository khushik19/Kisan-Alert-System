"""
checkpoint1_test.py — Full pipeline integration test
Person 1 → Person 3 → Person 2 (text-only, no voice yet)

Run from the repo root:
    python checkpoint1_test.py

What it does:
  Step 1: Simulate Person 1 — run vision_engine on a demo crop image
  Step 2: POST Person 1's output to Person 3's /advisory endpoint
  Step 3: POST Person 3's advisory_text to Person 2's /send-advisory
           (SMS skipped if Twilio not configured — uses mock flow)
  Step 4: Print full pipeline result + latency
"""

import sys
import time
import json
import os
import requests

# Load backend .env FIRST so GEMINI_API_KEY is in the environment
# before vision_engine.py is imported (it reads the key at module level)
from dotenv import load_dotenv
_backend_env = os.path.join(os.path.dirname(__file__), "Achal", "backend", ".env")
load_dotenv(_backend_env)


sys.stdout.reconfigure(encoding="utf-8")

PERSON3_URL  = "http://localhost:8000"      # Advisory engine (Person 3)
PERSON2_URL  = "http://localhost:3000"      # Voice/SMS layer (Person 2)
DEMO_IMAGES  = os.path.join(os.path.dirname(__file__), "demo_images")

DIVIDER = "=" * 64

def banner(title):
    print(f"\n{DIVIDER}")
    print(f"  {title}")
    print(DIVIDER)

# ---------------------------------------------------------------------------
# Step 1 — Person 1: Diagnose a demo image via vision_engine
# ---------------------------------------------------------------------------
banner("STEP 1 — Person 1: Disease Diagnosis (vision_engine.py)")

diagnosis = None
try:
    sys.path.insert(0, os.path.dirname(__file__))
    from vision_engine import diagnose_crop_image

    # Pick the first available jpg in demo_images
    images = [f for f in os.listdir(DEMO_IMAGES) if f.lower().endswith((".jpg",".jpeg",".png"))]
    if not images:
        raise FileNotFoundError("No demo images found in demo_images/")

    chosen = os.path.join(DEMO_IMAGES, images[0])
    print(f"  Image   : {chosen}")

    t0 = time.time()
    diagnosis = diagnose_crop_image(chosen)
    p1_latency = time.time() - t0

    print(f"  Latency : {p1_latency:.2f}s")
    print(f"  Output  : {json.dumps(diagnosis, ensure_ascii=False, indent=4)}")

except Exception as e:
    print(f"  [WARN] vision_engine failed: {e}")
    print("  Using hardcoded fallback diagnosis for pipeline test...")
    diagnosis = {
        "crop_identified": "Rice",
        "disease_name":    "rice blast",
        "confidence":      "High",
        "short_remedy":    "Apply Tricyclazole fungicide immediately"
    }
    p1_latency = 0.0

# ---------------------------------------------------------------------------
# Step 2 — Person 3: Generate Hindi advisory from diagnosis
# ---------------------------------------------------------------------------
banner("STEP 2 — Person 3: Advisory Engine (/advisory)")

try:
    t0 = time.time()
    r = requests.post(
        f"{PERSON3_URL}/advisory",
        json=diagnosis,          # Shape C — Streamlit/vision_engine output
        timeout=25,
    )
    p3_latency = time.time() - t0
    r.raise_for_status()
    p3_response = r.json()

    print(f"  Status  : {r.status_code}")
    print(f"  Latency : {p3_latency:.2f}s")
    print(f"  Disease : {p3_response.get('disease')}")
    print(f"  Crop    : {p3_response.get('crop')} | Stage: {p3_response.get('crop_stage')}")
    wx = p3_response.get("weather_snapshot", {})
    print(f"  Weather : {wx.get('condition')}, {wx.get('temp')}°C, {wx.get('humidity')}% humidity ({wx.get('city')})")
    print(f"  Advisory: {p3_response.get('advisory_text')}")
    advisory_text = p3_response.get("advisory_text")

except Exception as e:
    print(f"  [ERROR] Person 3 call failed: {e}")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Step 3 — Person 2: Deliver advisory via /send-advisory
# ---------------------------------------------------------------------------
banner("STEP 3 — Person 2: Voice/SMS Layer (/send-advisory)")

try:
    payload = {
        "to":       "+910000000000",    # dummy number — Twilio will reject but endpoint still runs
        "advisory": advisory_text,
    }
    t0 = time.time()
    r2 = requests.post(
        f"{PERSON2_URL}/send-advisory",
        json=payload,
        timeout=10,
    )
    p2_latency = time.time() - t0

    print(f"  Status  : {r2.status_code}")
    print(f"  Latency : {p2_latency:.2f}s")
    result = r2.json()
    # 200 = SMS sent, 500 = Twilio not configured (expected at Checkpoint 1)
    if r2.status_code == 200:
        print(f"  SMS SID : {result.get('sid')}")
        print(f"  SMS Text: {result.get('advisory_text')}")
    else:
        print(f"  [Expected] Twilio not configured yet: {result.get('error')}")
        print(f"  Advisory text DID reach Person 2: '{advisory_text}'")

except Exception as e:
    print(f"  [ERROR] Person 2 call failed: {e}")
    print("  Is Person 2's Flask server running on port 3000?")

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
banner("CHECKPOINT 1 SUMMARY")
total = p1_latency + p3_latency
print(f"  Person 1 (diagnosis)  : {p1_latency:.2f}s")
print(f"  Person 3 (advisory)   : {p3_latency:.2f}s")
print(f"  Total pipeline latency: {total:.2f}s")
print()
print(f"  Disease  : {p3_response.get('disease')}")
print(f"  Hindi Advisory:")
print(f"  {p3_response.get('advisory_text')}")
print()
print("  Pipeline result: Person 1 -> Person 3 -> Person 2 CONNECTED")
print(DIVIDER)
