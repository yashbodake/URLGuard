# URLGuard — Phishing & Malicious URL Classifier

A FastAPI service and CLI tool that classifies URLs as **PHISHING** or **LEGITIMATE** using a Random Forest model trained on 15 structural and lexical features.

##  Tech Stack
- FastAPI + Uvicorn
- scikit-learn (Random Forest)
- tldextract, SHAP (explainability)
- Typer (CLI)
- pytest (testing)

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Download dataset (run once)
python scripts/download_data.py

# 3. Train model (run once)
python scripts/train.py

# 4. Run API server
uvicorn app.main:app --reload --port 8002

# 5. Use CLI
python cli.py "https://paypal-security-update.xyz/login"
```

## Dataset
Uses the PhiUSIIL Phishing URL Dataset from UCI ML Repository (~235k URLs).

## Project Structure
- `app/features/` — URL feature extraction (Day 1)
- `app/model/` — Model training, scoring, and SHAP explainability (Day 2)
- `app/api/` — FastAPI routers and endpoints (Day 3)
- `scripts/` — Data download and training scripts
- `tests/` — Unit tests (pytest)
