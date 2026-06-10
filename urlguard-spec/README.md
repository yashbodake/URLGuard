# URLGuard — Phishing & Malicious URL Classifier

A FastAPI + CLI tool that classifies URLs as phishing or legitimate using a
Random Forest trained on ~235k labelled URLs. Extracts 15 structural and lexical
features from the URL string alone — no network calls, no browser, fully offline.
Includes SHAP-based feature importance to explain every prediction.

## Quick Start

```bash
# 1. Install
git clone <repo> && cd urlguard
pip install -r requirements.txt

# 2. Download dataset (one time, ~50MB)
python scripts/download_data.py

# 3. Train model (one time, ~2 minutes)
python scripts/train.py

# 4. Start API
cp .env.example .env
uvicorn app.main:app --reload --port 8002

# 5. Score a URL via API
curl -X POST http://localhost:8002/predict \
  -H "Content-Type: application/json" \
  -d '{"url": "https://paypal-security-update.xyz/verify/login"}'

# 6. Score via CLI
python cli.py "https://paypal-security-update.xyz/verify/login"
python cli.py "https://www.google.com"
```

## Tech Stack
- **FastAPI 0.115** — API framework
- **scikit-learn 1.5** — Random Forest classifier
- **tldextract 5.1** — URL parsing (domain, subdomain, TLD)
- **SHAP 0.45** — Feature importance (TreeExplainer)
- **Typer 0.12** — CLI framework
- **Pydantic v2** — Request/response validation

## API Endpoints
| Method | Path | Description |
|---|---|---|
| POST | `/predict` | Score a single URL |
| POST | `/predict/batch` | Score up to 100 URLs |
| GET | `/model/info` | Model metadata and metrics |
| GET | `/health` | Liveness check |

Full docs: `http://localhost:8002/docs`

## The 15 Features
URL length, domain length, path length, dot count, hyphen count, @ symbols,
query param count, IP address detection, HTTPS flag, suspicious TLD flag,
subdomain depth, path depth, brand-in-subdomain flag, lexical diversity, digit ratio.

All extracted from the URL string alone — zero network calls.

## Model Performance (target)
| Metric | Target |
|---|---|
| F1 Score | > 0.93 |
| Recall (phishing) | > 0.95 |
| ROC-AUC | > 0.97 |

## Dataset
PhiUSIIL Phishing URL Dataset — 134,850 legitimate + 100,945 phishing URLs.
Source: UCI ML Repository. Not committed to git.

## Running Tests
```bash
pytest tests/ -v
pytest --cov=app tests/ --cov-report=term-missing
```

## For AI Agents
Start with `CLAUDE.md`, then `docs/PROGRESS.md`.
Feature contract in `docs/FEATURES.md` — most important doc.
Full spec in `docs/PRD.md`, `docs/ARCHITECTURE.md`, `docs/API_SPEC.md`.
