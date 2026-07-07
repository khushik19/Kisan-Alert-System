# Kisan Alert — Advisory Engine Backend

## Setup

```bash
cd d:\GDG\Kisan-Alert-System\Achal\backend

# 1. Create virtual environment
python -m venv venv

# 2. Activate it
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the server
uvicorn main:app --reload
```

Server runs at: http://127.0.0.1:8000

## Test the endpoint

### Swagger UI (auto-generated)
Open: http://127.0.0.1:8000/docs

### curl
```bash
curl -X POST http://127.0.0.1:8000/advisory \
  -H "Content-Type: application/json" \
  -d '{"disease": "rice blast", "confidence": 0.87, "crop": "rice"}'
```

### PowerShell
```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8000/advisory `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"disease": "rice blast", "confidence": 0.87, "crop": "rice"}'
```

## API Contracts

### Input (from Person 1 — Diagnosis)
```json
{
  "disease": "rice blast",
  "confidence": 0.87,
  "crop": "rice"
}
```

### Output (to Person 2 — Voice/SMS)
```json
{
  "advisory_text": "...",
  "language": "hi",
  "disease": "rice blast"
}
```
