# Person 3 — Backend / Advisory Engine Lead
### Kisan Alert — Track 4 | Build with AI: Code for Communities, Indore

---

## 0. Your Mission in One Sentence

Build a single working pipeline:

```
generate_advisory(diagnosis, weather, crop_stage) → localized Hindi action text
```

You are the **glue** between Person 1 (diagnosis) and Person 2 (voice/SMS delivery). If your piece doesn't work, nothing connects. If it does, the whole demo comes alive.

---

## 1. Before You Touch Code — Lock the Contracts (Hour 0)

Do NOT start building until you've agreed on these two contracts with your teammates. This is the #1 cause of last-minute integration bugs.

### Contract with Person 1 (Diagnosis → You)
Ask them to confirm they'll send you exactly this shape:
```json
{
  "disease": "rice blast",
  "confidence": 0.87,
  "crop": "rice"
}
```
If their output looks different, agree on the format NOW and write it down somewhere shared (a Slack pin, a shared doc, whatever).

### Contract with Person 2 (You → Voice/SMS)
Ask them what they need. A safe default to propose:
```json
{
  "advisory_text": "आपकी फसल में झुलसा रोग पाया गया है। कृपया आज शाम तक कवकनाशी का छिड़काव करें।",
  "language": "hi",
  "disease": "rice blast"
}
```

**Action item:** Get both confirmed in writing before Hour 1 ends.

---

## 2. Setup Checklist (Hour 0–1)

- [ ] Get a **Gemini API key** from [Google AI Studio](https://aistudio.google.com/) (free tier is enough)
- [ ] Get a **free OpenWeatherMap API key** (instant signup, no approval wait — use this instead of IMD)
- [ ] Pick your **demo region** — e.g. a district near Indore — and note its lat/long
- [ ] Pick your **demo crop** — pick ONE (e.g. rice or wheat), don't try to support multiple
- [ ] Decide language: **Python (FastAPI)** or **Node (Express)** — see note in Section 8
- [ ] Create your repo folder / scaffold the basic server
- [ ] Confirm contracts with Person 1 and Person 2 (Section 1)

---

## 3. Step-by-Step Build Order

Build and test each piece **in isolation** before wiring them together. Don't try to build the whole pipeline at once.

### Step 1 — Scaffold the backend service
Create a minimal server with one endpoint: `POST /advisory`

**Python (FastAPI) example:**
```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class DiagnosisInput(BaseModel):
    disease: str
    confidence: float
    crop: str

@app.post("/advisory")
def advisory(input: DiagnosisInput):
    # we'll fill this in step by step
    return {"advisory_text": "placeholder", "language": "hi"}
```

Run it locally, hit it with a test POST (Postman, curl, or `requests`), confirm it returns something. **Get this working before adding any real logic.**

---

### Step 2 — Weather fetch function
Write a standalone function that takes lat/long and returns a simple weather summary.

```python
import requests

def get_weather(lat, lon, api_key):
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"lat": lat, "lon": lon, "appid": api_key, "units": "metric"}
    r = requests.get(url, params=params)
    data = r.json()
    return {
        "condition": data["weather"][0]["main"],   # e.g. "Rain", "Clear"
        "temp": data["main"]["temp"],
        "humidity": data["main"]["humidity"]
    }
```

**Test it alone first** — print the output for your chosen demo region's coordinates. Confirm it returns sensible data before moving on.

---

### Step 3 — Crop-stage logic (keep it simple)
Don't overbuild this. Hardcode a few stages and simple rules — this is a minor credibility boost, not core functionality.

```python
CROP_STAGES = {
    "sowing": "early growth, vulnerable to pests",
    "vegetative": "leaf growth stage",
    "flowering": "sensitive stage — avoid pesticide if rain expected",
    "harvest": "near harvest, minimize chemical use"
}

def get_crop_stage_note(stage: str) -> str:
    return CROP_STAGES.get(stage, "growth stage unknown")
```

For the demo, you can even just hardcode `crop_stage = "flowering"` as a fixed input if there's no time to make it dynamic.

---

### Step 4 — The Gemini advisory prompt (your core AI piece)
This is the most important step — it's what actually generates the farmer-facing advice.

```python
import requests as req

def generate_advisory_text(disease, confidence, weather, crop_stage, gemini_api_key):
    prompt = f"""
You are an agricultural advisor speaking to a farmer over the phone in simple Hindi.

Disease detected: {disease} (confidence: {confidence})
Current weather: {weather['condition']}, {weather['temp']}°C, humidity {weather['humidity']}%
Crop stage: {crop_stage}

Give ONE short, clear, actionable sentence in simple spoken Hindi telling the farmer
exactly what to do next. No jargon. No English words. Maximum 2 sentences.
"""

    response = req.post(
        "https://api.anthropic.com/v1/messages" if False else
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={gemini_api_key}",
        json={"contents": [{"parts": [{"text": prompt}]}]}
    )
    result = response.json()
    return result["candidates"][0]["content"]["parts"][0]["text"].strip()
```

**Test this in isolation with 3–4 fake disease inputs** before connecting anything else:
- Rice blast + rainy weather + flowering stage
- Healthy crop (edge case — what does it say?)
- Wheat rust + dry weather + vegetative stage
- Low-confidence diagnosis (does it still give sensible advice?)

Read every output. If any come back weird, garbled, or in English, tighten the prompt wording and re-test. **Do this now, not during the live demo.**

---

### Step 5 — Wire it all together in your endpoint
Now combine Steps 2–4 into your `/advisory` endpoint from Step 1.

```python
@app.post("/advisory")
def advisory(input: DiagnosisInput):
    weather = get_weather(DEMO_LAT, DEMO_LON, WEATHER_API_KEY)
    crop_stage_note = get_crop_stage_note("flowering")  # or dynamic if time permits
    text = generate_advisory_text(
        input.disease, input.confidence, weather, crop_stage_note, GEMINI_API_KEY
    )
    return {"advisory_text": text, "language": "hi", "disease": input.disease}
```

Test this full endpoint yourself with a fake diagnosis payload before anyone else touches it.

---

### Step 6 — Build a hardcoded fallback (your safety net)
For each of your 3–4 tested disease scenarios, **save the good Gemini output as a hardcoded backup**. If Gemini is slow, errors out, or produces garbage live during judging, serve the cached version instead.

```python
FALLBACK_ADVISORY = {
    "rice blast": "आपकी फसल में झुलसा रोग पाया गया है। कृपया आज शाम तक कवकनाशी का छिड़काव करें।",
    "wheat rust": "गेहूं में रस्ट रोग की पुष्टि हुई है। तुरंत अनुशंसित फफूंदनाशक का प्रयोग करें।"
}
```

Wrap your Gemini call in a try/except that falls back to this dict on failure. **This single step is your best insurance against a live-demo crash.**

---

## 4. Integration Checkpoints

### Checkpoint 1 (Hour 4–5) — Text-only, no voice yet
- Person 1 sends you their **real** diagnosis output (not fake data)
- Confirm your endpoint correctly turns it into advisory text
- Confirm the JSON shape matches what Person 2 expects
- Fix any format mismatches immediately

### Checkpoint 2 (Hour 7–8) — Full pipeline test
- Photo in (Person 1) → your advisory text out → delivered via voice/SMS (Person 2)
- Run this end-to-end at least 3 times with different disease inputs
- Time how long the full round-trip takes — if it's slow, that's a demo risk

---

## 5. Your Full Timeline

| Hour | What You're Doing |
|---|---|
| 0–1 | API keys, lock contracts with Person 1 & 2, scaffold server |
| 1–2 | Build + test weather fetch (Step 2) in isolation |
| 2–3 | Build crop-stage logic (Step 3) + Gemini prompt (Step 4), test with fake inputs |
| 3–4 | Wire full endpoint together (Step 5), build fallback cache (Step 6) |
| 4–5 | **Checkpoint 1** — plug in Person 1's real diagnosis output |
| 5–7 | Support Person 2 connecting your output to voice/SMS layer |
| 7–8 | **Checkpoint 2** — full end-to-end pipeline test, fix bugs |
| 8–9 | Polish, re-test fallback paths, help with backup demo video |
| 9–10 | Final rehearsal |

---

## 6. Risks Specific to Your Piece — And Mitigations

| Risk | Mitigation |
|---|---|
| Gemini returns garbled/English/nonsense Hindi | Pre-test 3–4 scenarios in Step 4 before integration; tighten prompt wording |
| Gemini API is slow or times out live | Hardcoded fallback dict (Step 6) — always have a backup ready |
| OpenWeatherMap API key issues / rate limits | Get the key in Hour 0, test it immediately, don't wait |
| JSON shape mismatch with Person 1 or 2 | Lock contracts in Hour 0 (Section 1), re-confirm at Checkpoint 1 |
| Crop-stage logic overengineered, eats time | Hardcode it — it's a minor scoring factor, not core |

---

## 7. Definition of Done (for your piece)

- [ ] `/advisory` endpoint runs locally and responds to a POST request
- [ ] Weather fetch returns real data for your demo region
- [ ] Gemini prompt produces a clean, short, Hindi sentence for at least 3 tested diseases
- [ ] Fallback cache exists and triggers correctly if Gemini fails
- [ ] Output JSON matches exactly what Person 2 needs
- [ ] Tested end-to-end with Person 1's real diagnosis output (Checkpoint 1)
- [ ] Tested end-to-end with Person 2's voice/SMS delivery (Checkpoint 2)
- [ ] You know your own worst-case output for each of the 3–4 demo scenarios by heart, in case you need to explain it live

---

## 8. One Decision to Make Right Now

**Python (FastAPI) vs Node (Express)?**

- Python is the more natural fit for Gemini's SDK and has more copy-paste-able examples.
- Node might match Person 2's stack better if they're using Dialogflow/Twilio libraries that are JS-first.

Pick based on whichever makes it *easiest to talk to Person 2's code* — ask them before deciding.

---

*Person 3 — Backend/Advisory Engine Lead — Kisan Alert, Track 4, Build with AI: Code for Communities, Indore Edition*
