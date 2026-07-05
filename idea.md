# Kisan Alert — AI Voice & SMS Crop Advisory
### Track 4 | Build with AI: Code for Communities — Indore Edition
### Team Size: 4 | Status: Starting from scratch

---

## 0. National Evaluation Criteria (keep this in mind at every step)

| Parameter | Weight | What Judges Look For |
|---|---|---|
| Problem-Solution Fit | 20% | Does it directly address the MP-submitted problem with the right scope? |
| AI / Technical Execution | 25% | Is the AI doing real, functional work? Does the prototype work end-to-end? |
| Deployability & Scalability | 25% | Could this realistically run in a real PHC, constituency, or district within weeks? |
| Inclusivity & Accessibility | 15% | Multilingual support, voice/low-literacy access, low-connectivity design |
| Impact Potential | 10% | How many citizens benefit, and how meaningfully? |
| Presentation & Clarity | 5% | Can a non-technical MP's office understand the value in 5 minutes? |

**Implication for time allocation:** AI Execution + Deployability together are 50% of your score. Spend the majority of your hours making the diagnosis → advisory → delivery pipeline actually work end-to-end, using tools that are realistically deployable (the official Google Cloud stack below) — not on deck polish, which is only 5% of the score.

---

## 1. Problem Statement

Farmers in rural India — especially small and marginal farmers without smartphones — have no easy way to get:
- Real-time crop disease diagnosis
- Localized, actionable advisory (irrigation, pesticide, sowing timing)
- Guidance in their own language

Existing AI agri-tools assume a smartphone, app literacy, and internet connectivity — none of which hold for a large share of India's farmers. The result: farmers rely on guesswork, delayed government helplines, or word-of-mouth, often too late to prevent crop loss.

**Core ask (Track 4 brief):** Build a voice & SMS crop advisory in Indic languages with AI disease diagnosis from farmer photos — designed for low-connectivity, non-smartphone farmers.

---

## 2. Solution Overview

A system with **two farmer-facing input channels** (photo submission + voice/SMS query) and **one AI advisory brain**, delivering short, actionable guidance entirely by voice or text message — no app, no smartphone, no data plan required.

### Core User Flow
```
Farmer has a problem (disease / general query)
        │
        ├── Path A: Has a photo (via WhatsApp/MMS/shared kiosk phone)
        │      → Gemini Vision diagnoses disease/pest
        │      → Advisory Engine generates action
        │      → Delivered via SMS or callback voice message
        │
        └── Path B: No photo, just a question or general check-in
               → Farmer gives a missed call (IVR)
               → System calls back, asks simple menu questions (voice, local language)
               → Weather/crop-stage based advisory generated
               → Delivered via voice (TTS) during the same call
```

---

## 3. What We're Building (Hackathon Scope)

Given time constraints, scope this as a **working demo of the full pipeline**, not a production telecom deployment. It's fine — and expected — to simulate the telecom layer (e.g., use a Twilio/Exotel trial number instead of a real IVR shortcode).

### MVP Components
1. **Disease Diagnosis Module** — Upload/send a crop photo → Gemini Vision returns disease name + confidence + basic remedy.
2. **Voice/IVR Simulation** — A number farmers can call (Twilio trial or web-based call simulator) that plays a menu and responds with a TTS advisory.
3. **SMS Delivery** — Advisory text sent back via SMS gateway (Twilio SMS API works for demo purposes).
4. **Advisory Engine** — A Gemini prompt/chain that turns raw model output (disease name, weather data, crop stage) into one short, plain-language action line, translated into Hindi (and one more Indic language if time permits).
5. **Simple Web Dashboard (optional, for judges)** — Shows incoming queries, diagnosis results, and advisories sent — this is your "show, don't tell" screen during the pitch even though farmers never see it.

### Explicitly Out of Scope for the Hackathon
- Real telecom shortcode / production IVR integration
- Support for all Indic languages (pick 1–2 max: Hindi + one regional)
- Handling multiple crop types robustly (pick 1 crop — e.g., rice or wheat — as your demo crop)
- Offline-first mobile app (not needed; this is a phone-call/SMS system by design)

---

## 4. Tech Stack (aligned to official hackathon tools list)

Using the official Google-native stack matters directly for your **Deployability & Scalability score (25%)** — it signals the prototype could realistically plug into government/telecom infrastructure, not just a hackathon sandbox.

| Layer | Tool |
|---|---|
| Disease diagnosis (photo) | Gemini API multimodal, or Vertex AI Vision |
| Advisory generation | Gemini API (text) |
| Prompt prototyping | Google AI Studio (fast iteration before wiring into backend) |
| Voice/SMS conversational flow | Dialogflow (handles both voice IVR-style menus and SMS/chat flows) |
| Speech-to-Text / Text-to-Speech | Cloud Speech-to-Text and Cloud Text-to-Speech (Hindi + regional voice models) |
| Translation / localization | Cloud Translation API |
| Citizen access channel | WhatsApp Business API or SMS gateway (for photo submission + advisory delivery) |
| Backend / orchestration | Cloud Functions or Cloud Run (serverless, fast to deploy) |
| Data storage / auth | Firebase (Firestore + Hosting) |
| Model fine-tuning (optional, if time allows) | Vertex AI |
| Weather data | IMD weather data (official) — fallback: OpenWeatherMap if IMD access is slow to set up |
| Crop/agriculture reference data | State agriculture department datasets (check data.gov.in for MP-specific datasets) |
| Dashboard (for judges) | Simple React app hosted on Firebase Hosting — don't over-invest, this is 5% of score |

**Fallback note:** If Dialogflow or WhatsApp Business API approval takes too long to set up mid-hackathon, it's fine to simulate the same flow with a simpler tool (e.g., a basic web form mimicking an SMS conversation) — just be transparent about this in your pitch as "final architecture," since judges are scoring the *design's* deployability, not requiring every piece to be production-wired in a few hours.

---

## 5. Team of 4 — Work Division

### Person 1 — AI/ML Lead: Disease Diagnosis
- Set up Gemini API (multimodal) access via Google AI Studio for fast prompt iteration; move to Vertex AI Vision if more control/fine-tuning is needed.
- Collect 10–15 sample crop disease images (rice/wheat blight, planthopper damage, etc.) from public datasets (e.g., PlantVillage) for demo/testing.
- Build the prompt pipeline: image in → {disease name, confidence, short remedy} out.
- Test edge cases (blurry photo, healthy crop photo, wrong crop) so the demo doesn't break live.
- **Deliverable:** A callable function/API endpoint: `diagnose(image) → {disease, remedy}`.

### Person 2 — Voice/Telephony Lead
- Set up Dialogflow for the conversational flow (voice menu + SMS/chat flow) — this is the officially recommended tool for this exact use case.
- Set up WhatsApp Business API (or an SMS gateway) as the citizen access channel for both photo submission and advisory delivery.
- Integrate Cloud Speech-to-Text (if capturing spoken input) and Cloud Text-to-Speech for Hindi voice playback.
- If WhatsApp Business API approval is slow, fall back to a simulated flow (e.g., a simple web form standing in for the SMS conversation) and note it as a placeholder for the pitch.
- **Deliverable:** A working demo channel (WhatsApp/SMS or simulated) where a judge can submit a photo and receive a spoken/text advisory back.

### Person 3 — Backend/Advisory Engine Lead
- Build the orchestration backend on Cloud Functions or Cloud Run that ties everything together: receives diagnosis result + weather/crop data → calls Gemini to generate final advisory text → sends to Person 2's voice/SMS layer.
- Fetch weather data from IMD (official source for this track); fall back to OpenWeatherMap if IMD access/setup is too slow for the timeframe.
- Pull in any available state agriculture department dataset (check data.gov.in) to make crop-stage assumptions more credible for the demo.
- Handle translation via Cloud Translation API (or a Gemini prompt as a simpler fallback: "convert this advisory into simple spoken Hindi").
- **Deliverable:** One orchestration endpoint: `generate_advisory(diagnosis, weather, crop_stage) → localized action text`.

### Person 4 — Dashboard, Data & Pitch Lead
- Build a lightweight dashboard (Streamlit/React) showing: incoming farmer queries, diagnosis results, advisories sent — for judges to see the system "thinking."
- Prepare the pitch deck (reuse/adapt the existing slide structure: Problem → Solution → Architecture → Impact → Business Value).
- Coordinate the live demo script (which photo to use, what number to call, in what order) so the 3–5 min demo runs smoothly without live bugs.
- Own the README and this project doc — keep it updated as scope changes.
- **Deliverable:** Dashboard, final pitch deck, and demo script.

> Everyone should test their component individually first, then do 2 integration passes as a team (once at the halfway point, once 1 hour before submission) to catch handoff bugs early.

---

## 6. Suggested Timeline (assuming a ~10–12 hr hackathon day)

| Time | Milestone |
|---|---|
| Hour 0–1 | Finalize scope, split tasks, set up repo/API keys (Gemini, Twilio, OpenWeatherMap) |
| Hour 1–4 | Each person builds their component in isolation (diagnosis, voice/SMS, backend, dashboard) |
| Hour 4–5 | **Integration Checkpoint 1** — connect diagnosis → backend → advisory text (text-only, no voice yet) |
| Hour 5–7 | Add voice/SMS delivery layer; connect end-to-end |
| Hour 7–8 | **Integration Checkpoint 2** — full pipeline test: photo in → advisory out via voice/SMS |
| Hour 8–9 | Bug fixes, polish dashboard, rehearse demo |
| Hour 9–10 | Finalize pitch deck, record backup demo video (in case live demo fails) |
| Hour 10+ | Submit + final rehearsal |

**Always record a backup demo video around hour 9** — live telecom/API demos are the most likely thing to break in front of judges.

---

## 7. Demo Script (for judges)

1. Show the problem slide (10 sec) — farmer with no smartphone, disease unnoticed till too late.
2. **Live/recorded call:** Dial the number → judge hears menu in Hindi → gets a sample advisory read aloud.
3. **Live/recorded photo:** Send a sample diseased crop photo via WhatsApp/MMS → show diagnosis + SMS advisory arriving on a phone.
4. Show the dashboard briefly — "this is what's happening behind the scenes."
5. Close with impact + scalability slide.

---

## 8. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Twilio/telecom setup takes longer than expected | Start this task first (Person 2), have a fallback: pre-recorded call demo video |
| Gemini Vision misclassifies on stage | Curate and pre-test 3–4 known-good sample images before the live demo |
| Hindi TTS sounds robotic/unclear | Keep advisory sentences short and simple; test audio clarity early |
| Team runs out of time for polish | Dashboard and pitch deck are lowest priority — cut these first if behind schedule |

---

## 9. Societal & Business Value (for pitch)

- **Economic Impact** — Faster disease detection reduces crop loss and input waste.
- **Social Value** — Reaches non-smartphone, low-literacy farmers who are excluded from most agri-tech today.
- **Environmental Benefit** — Targeted pesticide/fertilizer advice reduces overuse.
- **Scalability** — Same pipeline extends to other crops, regions, and languages by swapping the diagnosis dataset and TTS voice model.
- **Long-Term Vision** — A voice-first AI helpline model that could plug into existing Kisan Call Centre infrastructure.

---

*Team: Cosmos — Track 4, Build with AI: Code for Communities, Indore Edition*
