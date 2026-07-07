# DailyLotto Prediction Platform

## Backend (FastAPI + SQLite)
- API server: `backend/` directory
- Run: `cd backend && pip install -r requirements.txt && uvicorn main:app --host 0.0.0.0 --port 8000`
- Seed DB: `cd backend && python seed.py`
- Train LSTM: `cd backend && python train.py`
- Deploy on Render: `backend/render.yaml`

## Frontend (Next.js 14)
- App: `frontend/` directory
- Run: `cd frontend && npm install && npm run dev`
- API URL set in `frontend/.env.local` (NEXT_PUBLIC_API_URL)
- Deploy on Vercel: root `vercel.json`

## Endpoints
| Endpoint | Description |
|----------|-------------|
| GET / | Health check |
| GET /draws/latest | Latest draw result |
| GET /draws/recent?days=7 | Recent draws |
| GET /predict/frequency | Frequency analysis + hot numbers |
| GET /predict/markov | Markov chain prediction |
| GET /predict/lstm | LSTM neural network prediction |
| POST /checker | Check ticket numbers vs history |
| GET /tracker | Past predictions vs actuals |
| GET /tracker/win-rates | Win rate stats per method |
| POST /seed | Re-download CSV + scrape latest |
| POST /retrain | Seed + store predictions for today |
| POST /backfill | Backfill match counts for past predictions |
