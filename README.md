# StreetSignals.ai

Institutional-grade earnings call script analyzer. Run your draft through 12 research-backed analyses before a single analyst listens.

## Architecture

- **Backend**: FastAPI (Python 3.11) — wraps the existing analysis engine
- **Frontend**: React 18 + Tailwind CSS + Vite
- **Deployment**: Docker Compose, Railway-ready

## Quick Start (Development)

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The Vite dev server proxies `/api/*` to `localhost:8000`.

Open [http://localhost:5173](http://localhost:5173) in your browser.

## Docker Compose

```bash
docker-compose up --build
```

- Frontend: [http://localhost:3000](http://localhost:3000)
- Backend API: [http://localhost:8000](http://localhost:8000)

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/analyze` | Analyze a transcript (file upload or text) |
| GET | `/api/export/pdf/{session_id}` | Download PDF report |
| GET | `/api/export/word/{session_id}` | Download Word report |
| GET | `/api/export/json/{session_id}` | Download JSON results |

## Deployment (Railway)

1. Push to GitHub
2. Connect repo in Railway dashboard
3. Railway auto-detects `docker-compose.yml`
4. Add custom domain `streetsignals.ai` in Railway Settings > Custom Domain
5. Configure DNS CNAME records per Railway instructions
6. SSL is auto-provisioned via Let's Encrypt

## Analysis Dimensions

1. Sentiment Score (Loughran-McDonald dictionary)
2. Confidence Detection (Larcker-Zakolyukina framework)
3. Ownership Analysis (first-person language)
4. Clarity Score (readability metrics)
5. Red Flag Detection (deception markers)
6. Analyst Q&A Prediction (50-topic engine)
7. Negative Interpretation Scan (18 patterns)
8. Litigation Risk (PSLRA safe harbor)
9. Activist Trigger Analysis
10. Guidance Clarity Assessment
11. Legal Context Awareness
12. Historical Comparison
