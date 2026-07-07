"""
vision_engine.py — Person 1: Disease Diagnosis Module
Uses Gemini 2.0 Flash (multimodal) to identify crop diseases from images.

Deliverable: diagnose_crop_image(image) -> {disease_name, confidence, crop_identified, short_remedy}
"""

import json
import os

from google import genai
from google.genai import types
import PIL.Image

# ---------------------------------------------------------------------------
# API key — reads GEMINI_API_KEY from environment (set in backend/.env or shell)
# ---------------------------------------------------------------------------
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("WARNING: GEMINI_API_KEY environment variable not found. The API call will fail.")

client = genai.Client(api_key=api_key)

# Model fallback chain — 2.5-flash has a separate quota pool from 2.0-flash
VISION_MODELS = [
    "gemini-2.5-flash",      # primary — largest free quota
    "gemini-2.0-flash",      # fallback
    "gemini-2.0-flash-lite", # last resort
]

# ---------------------------------------------------------------------------
# System prompt — forces strict JSON output for clean backend handoff
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """
You are an expert agricultural plant pathologist. Analyze the provided image of a crop.
1. Identify the crop and the disease or pest present.
2. Determine your confidence level (High, Medium, Low).
3. Provide a single, short, actionable remedy (under 15 words) using accessible treatments.
4. If the image shows a healthy plant, state 'Healthy Crop' for the disease name.
5. If the image is not a plant or is entirely blurry, set the disease name to 'Invalid Image'
   and the remedy to 'Please submit a clear photo of the crop leaf.'

You must respond strictly in valid JSON format with exactly these keys:
"crop_identified", "disease_name", "confidence", "short_remedy"
""".strip()

# ---------------------------------------------------------------------------
# Core function
# ---------------------------------------------------------------------------
def diagnose_crop_image(image_input) -> dict:
    """
    Accepts either a string (file path) or a PIL.Image object.
    Calls Gemini 2.0 Flash multimodal and returns a parsed Python dictionary.

    Returns:
        {
            "crop_identified": "Rice",
            "disease_name":    "rice blast",
            "confidence":      "High",
            "short_remedy":    "Apply Tricyclazole fungicide spray immediately."
        }
    """
    try:
        if isinstance(image_input, str):
            img = PIL.Image.open(image_input)
        else:
            img = image_input
    except Exception as e:
        print(f"Error opening image: {e}")
        return {"crop_identified": "Unknown", "disease_name": "Invalid Image",
                "confidence": "Low", "short_remedy": "Please submit a clear photo of the crop leaf."}

    last_error = None
    for model in VISION_MODELS:
        try:
            response = client.models.generate_content(
                model=model,
                contents=[SYSTEM_PROMPT, img],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                ),
            )
            result_dict = json.loads(response.text)
            print(f"[vision] Diagnosed with {model}")
            return result_dict
        except Exception as e:
            print(f"[vision] {model} failed: {e}")
            last_error = e

    print(f"[vision] All models failed. Last error: {last_error}")
    return {
        "crop_identified": "Unknown",
        "disease_name":    "API Error",
        "confidence":      "Low",
        "short_remedy":    "System busy or API key missing. Please try again.",
    }


# ---------------------------------------------------------------------------
# Quick local test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    # Load backend .env so the key is available when running standalone
    try:
        from dotenv import load_dotenv
        backend_env = os.path.join(os.path.dirname(__file__), "backend", ".env")
        if not os.path.exists(backend_env):
            backend_env = os.path.join(os.path.dirname(__file__), ".env")
        load_dotenv(backend_env)
        # Re-initialise client with the loaded key
        _key = os.environ.get("GEMINI_API_KEY", "")
        client = genai.Client(api_key=_key)
    except ImportError:
        pass

    sys.stdout.reconfigure(encoding="utf-8")
    demo_dir = os.path.join(os.path.dirname(__file__), "demo_images")
    images = [f for f in os.listdir(demo_dir) if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))]

    if not images:
        print("No demo images found in demo_images/")
    else:
        test_path = os.path.join(demo_dir, images[0])
        print(f"Testing vision_engine with: {test_path}")
        result = diagnose_crop_image(test_path)
        print("\nDiagnosis Output:")
        print(json.dumps(result, indent=2, ensure_ascii=False))