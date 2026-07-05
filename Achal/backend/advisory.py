"""
advisory.py — Step 4: Gemini advisory prompt
Calls Gemini 2.0 Flash to generate a short Hindi action sentence
for the farmer, given disease diagnosis + weather + crop stage.

Includes a hardcoded FALLBACK_ADVISORY dict (Step 6 safety net)
so the demo survives even if Gemini is slow or returns garbage.
"""

import requests

# ---------------------------------------------------------------------------
# Step 6 safety net — pre-tested good Hindi outputs for demo diseases
# ---------------------------------------------------------------------------
FALLBACK_ADVISORY: dict[str, str] = {
    "rice blast": (
        "आपकी फसल में झुलसा रोग पाया गया है। "
        "कृपया आज शाम तक कवकनाशी का छिड़काव करें।"
    ),
    "wheat rust": (
        "गेहूं में रस्ट रोग की पुष्टि हुई है। "
        "तुरंत अनुशंसित फफूंदनाशक का प्रयोग करें।"
    ),
    "brown spot": (
        "फसल में भूरा धब्बा रोग है। "
        "खेत में पानी की निकासी सुनिश्चित करें और फफूंदनाशक छिड़कें।"
    ),
    "healthy": (
        "आपकी फसल स्वस्थ दिख रही है। "
        "नियमित सिंचाई जारी रखें और कीटों पर नज़र रखें।"
    ),
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
) -> str:
    """
    Call Gemini 2.0 Flash to produce a short, plain Hindi advisory sentence.

    Falls back to FALLBACK_ADVISORY (or a generic message) if the API
    call fails or returns an unusable response.
    """
    prompt = f"""
You are an agricultural advisor speaking to a farmer over the phone in simple Hindi.

Disease detected: {disease} (confidence: {confidence:.0%})
Current weather: {weather['condition']}, {weather['temp']}°C, humidity {weather['humidity']}%
Crop stage: {crop_stage}

Give ONE short, clear, actionable sentence in simple spoken Hindi telling the farmer
exactly what to do next. No jargon. No English words. Maximum 2 sentences.
""".strip()

    last_exc = None
    for model in GEMINI_MODELS:
        try:
            url = f"{GEMINI_BASE}{model}:generateContent"
            response = requests.post(
                url,
                params={"key": gemini_api_key},
                json={"contents": [{"parts": [{"text": prompt}]}]},
                timeout=10,
            )
            response.raise_for_status()
            result = response.json()
            text = result["candidates"][0]["content"]["parts"][0]["text"].strip()
            if len(text) < 10:
                raise ValueError("Gemini returned suspiciously short response")
            return text
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
    return (
        "फसल में समस्या का पता चला है। "
        "कृपया नज़दीकी कृषि केंद्र से संपर्क करें।"
    )


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
