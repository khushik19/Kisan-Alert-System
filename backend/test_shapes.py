import requests
import json
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")

BASE = "http://localhost:8000"

def post(label, payload):
    print(f"--- {label} ---")
    print("  Sending:", json.dumps(payload, ensure_ascii=False))
    try:
        r = requests.post(f"{BASE}/advisory", json=payload, timeout=25)
        d = r.json()
        disease_val = d.get("disease")
        advisory_val = d.get("advisory_text")
        print(f"  Status  : {r.status_code}")
        print(f"  Disease : {disease_val}")
        print(f"  Advisory: {advisory_val}")
    except Exception as e:
        print(f"  ERROR: {e}")
    print()
    time.sleep(1)

# Shape A - Person 1 direct (float confidence)
post("Shape A: Person 1 direct", {"disease": "rice blast", "confidence": 0.87, "crop": "rice"})

# Shape B - Person 2 voice layer
post("Shape B: Person 2 voice layer", {
    "type": "disease",
    "crop": "wheat",
    "diagnosis": {"disease": "blight", "confidence": 0.91, "remedy": "fungicide"},
    "location": "Indore village"
})

# Shape C - Person 1 Streamlit / vision_engine output (string confidence)
post("Shape C: Person 1 Streamlit output", {
    "crop_identified": "Rice",
    "disease_name": "Leaf Blast",
    "confidence": "High",
    "short_remedy": "Apply fungicide spray"
})

# Edge case - string confidence "Medium" in Shape A
post("Shape A + string confidence", {"disease": "wheat rust", "confidence": "Medium", "crop": "wheat"})

# Bad payload - should return 422
print("--- Bad payload (expect 422) ---")
r = requests.post(f"{BASE}/advisory", json={"foo": "bar"}, timeout=10)
print(f"  Status: {r.status_code}")
print(f"  Detail: {r.json().get('detail')}")
