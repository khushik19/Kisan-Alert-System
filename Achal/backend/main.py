import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

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
    version="1.0.0"
)

# --- Input contract (agreed with Person 1 / Diagnosis team) ---
class DiagnosisInput(BaseModel):
    disease: str        # e.g. "rice blast"
    confidence: float   # e.g. 0.87
    crop: str           # e.g. "rice"

# --- POST /advisory — main endpoint ---
@app.post("/advisory")
def advisory(input: DiagnosisInput):
    # Step 2: fetch real weather for demo region (Indore)
    try:
        weather = get_weather(DEMO_LAT, DEMO_LON, OPENWEATHER_API_KEY)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Weather fetch failed: {e}")

    # Step 3: get crop-stage context note
    stage_note = get_crop_stage_note(DEFAULT_STAGE)

    # Step 4: call Gemini to generate localized Hindi advisory
    advisory_text = generate_advisory_text(
        disease=input.disease,
        confidence=input.confidence,
        weather=weather,
        crop_stage=stage_note,
        gemini_api_key=GEMINI_API_KEY,
    )

    # Step 5: return the full response matching Person 2's contract
    return {
        "advisory_text": advisory_text,
        "language": "hi",
        "disease": input.disease,
        "crop_stage": DEFAULT_STAGE,
        "weather_snapshot": weather,      # useful for debugging / dashboard
    }

# --- Health check ---
@app.get("/health")
def health():
    return {"status": "ok", "service": "kisan-alert-advisory-engine"}
