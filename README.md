# KahveCell

Digital coffee subscription platform — Turkcell "Geleceği Yazan Kadınlar" software case.

**Stack:** Python + FastAPI · SQLite · React (Vite) · Leaflet

## Setup

### Backend

```bash
cd backend
python -m venv .venv                 # Mac/Linux: python3 -m venv .venv
.venv\Scripts\Activate.ps1           # Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
python seed.py                       # one-time demo data (safe to re-run)
uvicorn app.main:app --reload
```

Demo login: phone `5551234567`, OTP `1234` (active Starter subscription, 10 credits).

- Health check: http://localhost:8000/api/v1/health
- API docs (Swagger): http://localhost:8000/docs

> Windows: if activation fails with "running scripts is disabled", run once:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

App: http://localhost:5173
