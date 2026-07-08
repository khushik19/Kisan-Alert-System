import os
import sys
import io
import datetime
from typing import Any, Optional, Union
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from PIL import Image

from weather import get_weather
from crop_stage import get_crop_stage_note, DEFAULT_STAGE
from advisory import generate_advisory_text

load_dotenv()

# --- Config from .env ---
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
GEMINI_API_KEY      = os.getenv("GEMINI_API_KEY")
DEMO_LAT  = float(os.getenv("DEMO_LAT", 22.7196))
DEMO_LON  = float(os.getenv("DEMO_LON", 75.8577))
DEMO_CROP = os.getenv("DEMO_CROP", "rice")

app = FastAPI(
    title="Kisan Alert — Advisory Engine",
    description="Backend orchestration for crop disease advisory generation.",
    version="1.2.0"
)

# Allow dashboard (Streamlit) to call this API from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory query log — seeded with mock data so dashboard displays content immediately
query_log: list[dict] = [
    {
        "query_id": "Q-2026-001",
        "phone": "+91 98765 43210",
        "timestamp": "2026-07-05 10:15",
        "crop": "Paddy (Rice)",
        "photo_desc": "Leaf exhibiting wavy yellowing along edges",
        "photo_url": "https://images.unsplash.com/photo-1599599810769-bcde5a160d32?auto=format&fit=crop&w=300&q=80",
        "disease": "Bacterial Leaf Blight",
        "confidence": "94.5%",
        "remedy": "Spray Agrimycin-100 (0.2 g/L) + Copper Oxychloride (2.5 g/L) at 12-day intervals.",
        "advisory": "प्रिय किसान भाई, आपकी धान की फसल में बैक्टीरियल लीफ ब्लाइट (झुलसा रोग) के लक्षण हैं। कृपया 10 लीटर पानी में 0.2 ग्राम एग्रीमाइसिन-100 और 2.5 ग्राम कॉपर ऑक्सीक्लोराइड मिलाकर छिड़काव करें।",
        "language": "Hindi",
        "delivery": "SMS",
        "status": "✅ Sent"
    },
    {
        "query_id": "Q-2026-002",
        "phone": "+91 87654 32109",
        "timestamp": "2026-07-05 10:32",
        "crop": "Wheat",
        "photo_desc": "Orange/brown powdery pustules on leaves",
        "photo_url": "https://images.unsplash.com/photo-1592417817098-8f3d6eb19675?auto=format&fit=crop&w=300&q=80",
        "disease": "Brown Rust",
        "confidence": "89.2%",
        "remedy": "Spray Propiconazole 25 EC (Tilt) @ 1 ml/L of water.",
        "advisory": "किसान भाई, आपकी गेहूं की फसल में भूरा रतुआ (Brown Rust) के लक्षण हैं। इसके नियंत्रण हेतु प्रोपिकोनाजोल 25 EC का 1 मिलीलीटर प्रति लीटर पानी में मिलाकर छिड़काव करें।",
        "language": "Hindi",
        "delivery": "Voice Call",
        "status": "✅ Sent"
    },
    {
        "query_id": "Q-2026-003",
        "phone": "+91 76543 21098",
        "timestamp": "2026-07-05 11:02",
        "crop": "Tomato",
        "photo_desc": "Dark concentric spots on older leaves",
        "photo_url": "https://images.unsplash.com/photo-1530595467537-0b5996c41f2d?auto=format&fit=crop&w=300&q=80",
        "disease": "Early Blight",
        "confidence": "91.8%",
        "remedy": "Apply Chlorothalonil @ 2 g/L or Mancozeb @ 2.5 g/L.",
        "advisory": "టమోటా పంటకు ముందస్తు తెగులు (Early Blight) సోకినట్లు నిర్ధారణ అయింది. దీని నివారణకు లీటరు నీటికి 2.5 గ్రాముల మాంకోజెబ్ కలిపి పిచికారీ చేయండి.",
        "language": "Telugu",
        "delivery": "SMS",
        "status": "⏳ Pending"
    },
    {
        "query_id": "Q-2026-004",
        "phone": "+91 99887 76655",
        "timestamp": "2026-07-05 11:15",
        "crop": "Corn (Maize)",
        "photo_desc": "Healthy green leaves without any lesions",
        "photo_url": "https://images.unsplash.com/photo-1628352081506-83c4307476a8?auto=format&fit=crop&w=300&q=80",
        "disease": "Healthy (No Disease)",
        "confidence": "98.1%",
        "remedy": "Maintain standard irrigation and nitrogen application. No disease treatment required.",
        "advisory": "आपकी मक्के की फसल पूरी तरह स्वस्थ है। किसी रोगनाशक दवा की आवश्यकता नहीं है। नियमित सिंचाई करते रहें।",
        "language": "Hindi",
        "delivery": "Voice Call",
        "status": "✅ Sent"
    }
]

# ---------------------------------------------------------------------------
# Confidence normalizer
# Person 1 sends string ("High" / "Medium" / "Low")
# Person 3 internally uses float (0.0-1.0)
# ---------------------------------------------------------------------------
_CONFIDENCE_MAP = {"high": 0.90, "medium": 0.65, "low": 0.35}

def normalize_confidence(value: Any) -> float:
    """Convert string or numeric confidence to a float in [0, 1]."""
    if isinstance(value, str):
        return _CONFIDENCE_MAP.get(value.strip().lower(), 0.65)
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.65


# ---------------------------------------------------------------------------
# Normalizer: detect payload shape and extract (disease, confidence, crop)
# ---------------------------------------------------------------------------
def _normalize(body: dict) -> tuple:
    """
    Supports three caller shapes:

    Shape A - Direct / Person 1 direct call:
      { "disease": "rice blast", "confidence": 0.87, "crop": "rice" }

    Shape B - Person 2 voice layer (voice_telephony/app.py):
      { "type": "disease", "crop": "wheat",
        "diagnosis": {"disease": "blight", "confidence": 0.91}, "location": "..." }

    Shape C - Person 1 Streamlit / vision_engine.py output:
      { "crop_identified": "Rice", "disease_name": "Leaf Blast",
        "confidence": "High", "short_remedy": "Apply fungicide" }

    Returns (disease: str, confidence: float, crop: str)
    """
    # Shape C - Streamlit / vision_engine output
    if "disease_name" in body:
        return (
            body["disease_name"],
            normalize_confidence(body.get("confidence", "Medium")),
            body.get("crop_identified", DEMO_CROP),
        )

    # Shape B - Person 2 / voice layer & Mobile App
    if "diagnosis" in body:
        diag    = body.get("diagnosis") or {}
        disease = diag.get("disease") or diag.get("disease_name") or "Unknown"
        conf    = normalize_confidence(diag.get("confidence", "Medium"))
        crop    = diag.get("crop") or body.get("crop") or DEMO_CROP
        return disease, conf, crop

    # Shape A - direct / Person 1 direct call
    if "disease" in body:
        return (
            body["disease"],
            normalize_confidence(body.get("confidence", 0.65)),
            body.get("crop", DEMO_CROP),
        )

    raise ValueError(
        "Unrecognised payload. Send one of: "
        "{disease, confidence, crop} | "
        "{type, crop, diagnosis} | "
        "{disease_name, confidence, crop_identified}"
    )


# Sentinel disease values that mean "no real diagnosis was made"
_INVALID_DISEASES = {"api error", "unknown", "invalid image", "error", ""}


# ---------------------------------------------------------------------------
# POST /advisory - unified endpoint (accepts all three shapes)
# ---------------------------------------------------------------------------
@app.post("/advisory")
async def advisory(request: Request):
    """
    Single endpoint that accepts payloads from Person 1 (direct or Streamlit)
    AND Person 2 (voice/SMS layer). Normalises all shapes internally.
    """
    try:
        body: dict = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Request body must be valid JSON.")

    # Detect + normalise payload shape
    try:
        disease, confidence, crop = _normalize(body)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    # --- Validation: reject sentinel / garbage disease names ---
    if disease.strip().lower() in _INVALID_DISEASES:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Disease value '{disease}' is not a valid diagnosis. "
                "Please submit a real crop image first."
            ),
        )

    # Step 2 - real weather
    try:
        weather = get_weather(DEMO_LAT, DEMO_LON, OPENWEATHER_API_KEY)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Weather fetch failed: {e}")

    # Step 3 - crop stage
    stage_note = get_crop_stage_note(DEFAULT_STAGE)

    # Step 4 - Gemini advisory
    advisory = generate_advisory_text(
        disease=disease,
        confidence=confidence,
        weather=weather,
        crop_stage=stage_note,
        gemini_api_key=GEMINI_API_KEY,
        crop=crop,
    )
    advisory_hindi   = advisory.get("hindi",   "")
    advisory_english = advisory.get("english", "")
    advisory_tip     = advisory.get("tip",     "")

    return {
        "advisory_text":    advisory_hindi,   # kept for backward-compat (SMS/voice layer uses this)
        "advisory_hindi":   advisory_hindi,
        "advisory_english": advisory_english,
        "tip":              advisory_tip,
        "language": "hi+en",
        "disease": disease,
        "crop": crop,
        "crop_stage": DEFAULT_STAGE,
        "weather_snapshot": weather,
    }


# ---------------------------------------------------------------------------
# GET / — Welcome endpoint
# ---------------------------------------------------------------------------
@app.get("/")
def read_root():
    return {
        "status": "active",
        "service": "Kisan Alert Advisory Engine API",
        "version": "1.2.1",
        "message": "Welcome! The API is running. Check /health for status.",
        "endpoints": ["/health", "/queries", "/diagnose", "/advisory"]
    }


# ---------------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------------
@app.get("/health")
def health():
    return {"status": "ok", "service": "kisan-alert-advisory-engine", "version": "1.2.1"}


# ---------------------------------------------------------------------------
# POST /diagnose — image upload → vision_engine → advisory (for dashboard Tab 4)
# ---------------------------------------------------------------------------
@app.post("/diagnose")
async def diagnose(file: UploadFile = File(...)):
    """
    Accepts a crop image upload, runs Person 1's vision_engine,
    then generates a Hindi advisory. Logs the result to query_log
    so the dashboard /queries feed updates in real-time.
    """
    # Import vision_engine (adds repo root to path so it can be found)
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)

    try:
        from vision_engine import diagnose_crop_image
    except ImportError as e:
        raise HTTPException(status_code=500, detail=f"vision_engine import failed: {e}")

    # Validate file is actually an image
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail=f"Uploaded file is not an image (got '{file.content_type}'). Please upload a JPG or PNG crop photo."
        )

    # Open the uploaded image
    try:
        image_bytes = await file.read()
        if len(image_bytes) == 0:
            raise ValueError("Uploaded file is empty.")
        img = Image.open(io.BytesIO(image_bytes))
        img.verify()  # Detect truncated/corrupt images early
        img = Image.open(io.BytesIO(image_bytes))  # Re-open after verify (verify closes the file)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image file: {e}")

    # Step 1 — Person 1 diagnosis
    diagnosis = diagnose_crop_image(img)
    disease    = diagnosis.get("disease_name", "Unknown")
    confidence = diagnosis.get("confidence", "Medium")
    crop       = diagnosis.get("crop_identified", DEMO_CROP)

    # --- Guard: if vision_engine could not produce a real diagnosis, return error ---
    if disease.strip().lower() in _INVALID_DISEASES:
        return {
            "error": True,
            "disease": disease,
            "message": (
                "The AI could not identify a crop disease from this image. "
                "Please upload a clear, well-lit photo of a crop leaf."
            ),
            "remedy": diagnosis.get("short_remedy", ""),
            "advisory_hindi":   "स्पष्ट फसल की पत्ती की फोटो भेजें। इस छवि से रोग की पहचान नहीं हो सकी।",
            "advisory_english": "Please send a clear photo of the crop leaf. Disease could not be identified from this image.",
            "advisory_text":    "स्पष्ट फसल की पत्ती की फोटो भेजें। इस छवि से रोग की पहचान नहीं हो सकी।",
        }

    # Step 2 — weather
    try:
        weather = get_weather(DEMO_LAT, DEMO_LON, OPENWEATHER_API_KEY)
    except Exception:
        weather = {"condition": "Unknown", "temp": 0, "humidity": 0, "city": "Indore"}

    # Step 3 — crop stage
    stage_note = get_crop_stage_note(DEFAULT_STAGE)

    # Step 4 — Gemini advisory
    advisory = generate_advisory_text(
        disease=disease,
        confidence=normalize_confidence(confidence),
        weather=weather,
        crop_stage=stage_note,
        gemini_api_key=GEMINI_API_KEY,
        crop=crop,
    )
    advisory_hindi   = advisory.get("hindi",   "")
    advisory_english = advisory.get("english", "")
    advisory_tip     = advisory.get("tip",     "")

    # Log to in-memory query store (dashboard reads this)
    entry = {
        "query_id":   f"Q-{datetime.datetime.now().strftime('%H%M%S')}",
        "phone":      "Dashboard Upload",
        "timestamp":  datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "crop":       crop,
        "photo_desc": f"Uploaded via dashboard — {file.filename}",
        "photo_url":  "https://images.unsplash.com/photo-1599599810769-bcde5a160d32?auto=format&fit=crop&w=300&q=80",
        "disease":    disease,
        "confidence": str(confidence),
        "remedy":     diagnosis.get("short_remedy", ""),
        "advisory":   advisory_hindi,
        "language":   "Hindi + English",
        "delivery":   "Dashboard",
        "status":     "✅ Sent",
    }
    query_log.append(entry)

    return {
        "disease":          disease,
        "confidence":       confidence,
        "crop":             crop,
        "remedy":           diagnosis.get("short_remedy", ""),
        "advisory_text":    advisory_hindi,
        "advisory_hindi":   advisory_hindi,
        "advisory_english": advisory_english,
        "tip":              advisory_tip,
        "weather":          weather,
    }


# ---------------------------------------------------------------------------
# GET & POST /queries — manage query history for the dashboard
# ---------------------------------------------------------------------------
@app.get("/queries")
def queries():
    """Returns all logged queries (real + simulated) for the dashboard."""
    return query_log


@app.post("/queries")
async def add_query(request: Request):
    """Allows the dashboard simulator to add new simulated queries into the feed."""
    try:
        query = await request.json()
        query_log.append(query)
        return {"status": "success", "added": query.get("query_id")}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


