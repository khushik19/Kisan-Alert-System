"""
crop_stage.py — Step 3: Crop-stage logic
Hardcoded stage descriptions used to enrich the Gemini advisory prompt.
Keep this simple — it's a credibility boost, not core functionality.
"""

CROP_STAGES: dict[str, str] = {
    "sowing":     "early growth, vulnerable to pests",
    "vegetative": "leaf growth stage",
    "flowering":  "sensitive stage — avoid pesticide if rain expected",
    "harvest":    "near harvest, minimize chemical use",
}

# Default for demo — override via request body if time permits
DEFAULT_STAGE = "flowering"


def get_crop_stage_note(stage: str) -> str:
    """
    Return a plain-English note for the given crop stage.
    Falls back to 'growth stage unknown' for unrecognised inputs.
    """
    return CROP_STAGES.get(stage.lower().strip(), "growth stage unknown")


# --- Quick standalone test ---
if __name__ == "__main__":
    test_stages = ["sowing", "vegetative", "flowering", "harvest", "unknown"]
    print("Crop-stage lookup test:")
    for s in test_stages:
        print(f"  {s!r:15} => {get_crop_stage_note(s)}")
