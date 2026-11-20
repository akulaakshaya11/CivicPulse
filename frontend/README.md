# CivicPulse — Impact Intelligence

A polished, responsive civic-issue prioritization dashboard built with React, Vite, Recharts and Lucide icons.

## Run it locally
1. Install Node.js 18+ (Node.js 20 LTS recommended).
2. Open a terminal in the `frontend` folder.
3. Run `npm install`
4. Run `npm run dev`
5. Open the localhost URL Vite prints (usually `http://localhost:5173`).

## Connect your FastAPI backend
Create `.env` from `.env.example` if you want to change the API URL. Default API base URL is `http://127.0.0.1:8000`.

In your existing `main.py`, add this import:
```python
from fastapi.middleware.cors import CORSMiddleware
```
Immediately after your existing `app = FastAPI(...)`, add:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
```
Do not create a second FastAPI app. Save the file and let Uvicorn reload.

Run the backend in a separate terminal:
```powershell
cd "$HOME\OneDrive\Desktop\civic\backend"
.\venv\Scripts\Activate.ps1
python -m uvicorn main:app --reload --reload-dir .
```

## Important data note
When the API is unreachable, the dashboard displays a clearly labeled sample preview so the design remains explorable. Sample trend and category charts are illustrative, not real statistics. The priority score is a provisional rule-based baseline, not a trained ML prediction or an objective verdict. Replace sample chart data with real aggregate endpoints before presenting the dashboard as live operational data.
