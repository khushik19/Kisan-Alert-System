"""
advisory.py — Step 4: Gemini advisory prompt
Calls Gemini Flash to generate bilingual (Hindi + English) advisories
for the farmer, given disease diagnosis + weather + crop stage.

Includes a hardcoded FALLBACK_ADVISORY dict (Step 6 safety net)
so the demo survives even if Gemini is slow or returns garbage.
"""

import json
import requests

# ---------------------------------------------------------------------------
# Step 6 safety net — fallback bilingual advisories for demo diseases
# ---------------------------------------------------------------------------
FALLBACK_ADVISORY: dict[str, dict] = {
    "rice blast": {
        "hindi":   "आपकी फसल में झुलसा रोग पाया गया है। कृपया आज शाम तक कवकनाशी का छिड़काव करें।",
        "english": "Rice blast disease detected. Apply fungicide spray before evening today.",
    },
    "wheat rust": {
        "hindi":   "गेहूं में रस्ट रोग की पुष्टि हुई है। तुरंत अनुशंसित फफूंदनाशक का प्रयोग करें।",
        "english": "Wheat rust confirmed. Apply the recommended fungicide immediately.",
    },
    "brown spot": {
        "hindi":   "फसल में भूरा धब्बा रोग है। खेत में पानी की निकासी सुनिश्चित करें और फफूंदनाशक छिड़कें।",
        "english": "Brown spot disease found. Ensure field drainage and apply fungicide.",
    },
    "sheath blight": {
        "hindi":   "फसल में शीथ ब्लाइट रोग पाया गया है। खेत में पानी कम करें और ट्राइकोडर्मा का छिड़काव करें।",
        "english": "Sheath blight detected. Reduce field water and spray Trichoderma.",
    },
    "alternaria pod blight": {
        "hindi":   "फसल में अल्टरनेरिया रोग है। तुरंत मैंकोजेब फफूंदनाशक का छिड़काव करें।",
        "english": "Alternaria blight found. Spray Mancozeb fungicide immediately.",
    },
    "blight": {
        "hindi":   "फसल में झुलसा रोग की पुष्टि हुई है। कृपया तुरंत कवकनाशी दवा का छिड़काव करें।",
        "english": "Blight disease confirmed. Apply fungicide medicine immediately.",
    },
    "healthy": {
        "hindi":   "आपकी फसल स्वस्थ दिख रही है। नियमित सिंचाई जारी रखें और कीटों पर नज़र रखें।",
        "english": "Your crop looks healthy. Continue regular irrigation and monitor for pests.",
    },
    "leaf curl": {
        "hindi":   "पत्तियों में मुड़ने की समस्या है। कीटनाशक का छिड़काव करें और खेत की नमी जांचें।",
        "english": "Leaf curl problem found. Apply insecticide and check field moisture.",
    },
}

GEMINI_MODELS = [
    "gemini-2.5-flash",   # primary — confirmed available on this key
    "gemini-2.0-flash",   # fallback
]
GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta/models/"


def generate_advisory_text(
    disease: str,
    confidence: float,
    weather: dict,
    crop_stage: str,
    gemini_api_key: str,
) -> dict:
    """
    Call Gemini Flash to produce bilingual advisories (Hindi + English).

    Returns a dict: { "hindi": "...", "english": "..." }

    Falls back to FALLBACK_ADVISORY (or generic messages) if the API
    call fails or returns an unusable response.
    """
    prompt = f"""
You are an agricultural advisor helping a farmer understand a crop disease.

Disease detected: {disease} (confidence: {confidence:.0%})
Current weather: {weather['condition']}, {weather['temp']}°C, humidity {weather['humidity']}%
Crop stage: {crop_stage}

Give ONE short, clear, actionable advisory (maximum 2 sentences each) in BOTH languages:
1. Simple spoken Hindi (no English words, easy for a rural farmer to understand)
2. Clear English (for reference by extension workers or digital displays)

Respond ONLY with valid JSON in exactly this format:
{{"hindi": "<Hindi advisory here>", "english": "<English advisory here>"}}
""".strip()

    last_exc = None
    for model in GEMINI_MODELS:
        try:
            url = f"{GEMINI_BASE}{model}:generateContent"
            response = requests.post(
                url,
                params={"key": gemini_api_key},
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"responseMimeType": "application/json"},
                },
                timeout=12,
            )
            response.raise_for_status()
            result = response.json()
            raw = result["candidates"][0]["content"]["parts"][0]["text"].strip()
            parsed = json.loads(raw)
            hindi   = parsed.get("hindi", "").strip()
            english = parsed.get("english", "").strip()
            if len(hindi) < 5 or len(english) < 5:
                raise ValueError("Gemini returned too-short advisory")
            print(f"[advisory] Bilingual advisory generated with {model}")
            return {"hindi": hindi, "english": english}
        except Exception as exc:
            print(f"[advisory] {model} failed ({exc}), trying next model...")
            last_exc = exc

    print("[advisory] All Gemini models failed. Using hardcoded fallback.")
    # Try exact match first, then partial match, then generic
    fallback = FALLBACK_ADVISORY.get(disease.lower().strip())
    if fallback:
        return fallback
    for key, val in FALLBACK_ADVISORY.items():
        if key in disease.lower():
            return val
    return {
        "hindi":   "फसल में समस्या का पता चला है। कृपया नज़दीकी कृषि केंद्र से संपर्क करें।",
        "english": "A crop problem was detected. Please contact your nearest agriculture center.",
    }


# ---------------------------------------------------------------------------
# Quick standalone test — run: python advisory.py
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import os
    import sys
    from dotenv import load_dotenv

    # Force UTF-8 output so Hindi text prints correctly on Windows
    sys.stdout.reconfigure(encoding="utf-8")

    load_dotenv()
    key = os.getenv("GEMINI_API_KEY", "")

    fake_weather = {"condition": "Rain", "temp": 30.0, "humidity": 82}

    test_cases = [
        ("rice blast",  0.87, fake_weather, "flowering"),
        ("wheat rust",  0.74, fake_weather, "vegetative"),
        ("brown spot",  0.65, fake_weather, "sowing"),
        ("healthy",     0.95, fake_weather, "harvest"),
        ("leaf curl",   0.40, fake_weather, "flowering"),   # low confidence / unknown
    ]

    print("=== Gemini Advisory Test ===\n")
    import time
    for disease, conf, wx, stage in test_cases:
        print(f"Disease : {disease} ({conf:.0%})")
        print(f"Weather : {wx['condition']} {wx['temp']}C  Humidity: {wx['humidity']}%")
        print(f"Stage   : {stage}")
        result = generate_advisory_text(disease, conf, wx, stage, key)
        print(f"Advisory: {result}")
        print("-" * 60)
        time.sleep(1)   # avoid 429 burst limit between test calls
