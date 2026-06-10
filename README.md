# URLGuard — Phishing & Malicious URL Classifier

A FastAPI service and CLI tool that classifies URLs as **PHISHING** or **LEGITIMATE** using a Random Forest model trained on 15 structural and lexical features.

**Portfolio angle**: Pure feature engineering from URL strings — no internet access, no browser, no scraping. Fast, offline, explainable. Includes SHAP-style feature importance so the API explains WHY a URL is flagged.

## Quick Start

```bash
# 1. Clone and install
pip install -r requirements.txt

# 2. Download the dataset (run once)
python scripts/download_data.py

# 3. Train the model (run once)
python scripts/train.py

# 4. Start the API server
uvicorn app.main:app --reload --port 8002

# 5. Score URLs via API
curl -X POST http://localhost:8002/predict \
  -H "Content-Type: application/json" \
  -d '{"url": "https://paypal-security-update.xyz/login"}'

# 6. Or score via CLI
python cli.py "https://paypal-security-update.xyz/login"
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/predict` | Score a single URL |
| `POST` | `/predict/batch` | Score up to 100 URLs |
| `GET` | `/model/info` | Model metadata and metrics |
| `GET` | `/health` | Health check |

### Single URL Prediction

```bash
curl -X POST http://localhost:8002/predict \
  -H "Content-Type: application/json" \
  -d '{"url": "https://paypal-security-update.xyz/verify/account/login?token=abc123"}'
```

**Response:**
```json
{
  "url": "https://paypal-security-update.xyz/verify/account/login?token=abc123",
  "label": "PHISHING",
  "risk_score": 0.87,
  "confidence": "HIGH",
  "top_features": [
    {"feature": "tld_is_suspicious", "shap_value": 0.31, "direction": "phishing"},
    {"feature": "num_hyphens", "shap_value": 0.24, "direction": "phishing"}
  ],
  "features": {
    "url_length": 79,
    "domain_length": 24,
    "path_length": 27,
    ...
  },
  "processing_ms": 18
}
```

### CLI Usage

```bash
# Score a URL
python cli.py "https://paypal-security-update.xyz/login"

# Output with coloured box
╔══════════════════════════════════════════════════╗
║  URLGuard Risk Assessment                        ║
╠══════════════════════════════════════════════════╣
║  URL:    https://paypal-security-update.xyz/...  ║
║  Label:  ⚠  PHISHING                            ║
║  Score:  0.87  (HIGH confidence)                 ║
╠══════════════════════════════════════════════════╣
║  Top contributing features:                      ║
║  + tld_is_suspicious    →  +0.31 (💀 phishing)  ║
║  + num_hyphens          →  +0.24 (💀 phishing)  ║
╚══════════════════════════════════════════════════╝

# Exit codes (pipeable):
# 0 = LEGITIMATE, 1 = PHISHING, 2 = error
python cli.py "http://evil.tk/steal" && echo "safe" || echo "danger"
```

## Dataset

Uses the [PhiUSIIL Phishing URL Dataset](https://archive.ics.uci.edu/dataset/967/phiusiil+phishing+url+dataset) from UCI ML Repository (~236k URLs: 134k legitimate + 101k phishing).

Run `python scripts/download_data.py` to download automatically.

## The 15 Features

| # | Feature | What it measures |
|---|---------|-----------------|
| 0 | `url_length` | Total URL length — long URLs hide true destination |
| 1 | `domain_length` | Registered domain length — long domains suspicious |
| 2 | `path_length` | URL path length — deep paths are unusual |
| 3 | `num_dots` | Count of `.` in URL — many dots = subdomain abuse |
| 4 | `num_hyphens` | Count of `-` in URL — hyphens in domain = phishing signal |
| 5 | `num_at_symbols` | Count of `@` — tricks URL parsers |
| 6 | `num_query_params` | Number of query parameters — tracking/obfuscation |
| 7 | `has_ip_address` | Domain is raw IPv4 — evasion signal |
| 8 | `has_https` | Uses HTTPS — weak but useful signal |
| 9 | `tld_is_suspicious` | TLD is in abuse-heavy list (`.xyz`, `.tk`, `.ml`, etc.) |
| 10 | `subdomain_depth` | Number of subdomain levels |
| 11 | `path_depth` | Number of path segments |
| 12 | `has_brand_in_subdomain` | Known brand in subdomain ≠ domain = phishing |
| 13 | `lexical_diversity` | Unique chars / total length — low = generated |
| 14 | `digit_ratio` | Digit chars / total length — high = random domain |

## Project Structure

```
urlguard/
├── app/
│   ├── main.py              ← FastAPI entry point
│   ├── config.py            ← Pydantic settings
│   ├── features/
│   │   ├── extractor.py     ← URL feature extraction (pure, no I/O)
│   │   ├── constants.py     ← FEATURE_NAMES, SUSPICIOUS_TLDS, BRAND_NAMES
│   │   └── validator.py     ← URL format validation
│   ├── model/
│   │   ├── scorer.py        ← Model singleton: load, score, predict
│   │   ├── explainer.py     ← SHAP TreeExplainer for feature importance
│   │   └── schemas.py       ← Pydantic v2 request/response schemas
│   └── api/
│       ├── router_predict.py ← POST /predict, /predict/batch
│       ├── router_model.py   ← GET /model/info, /health
│       └── dependencies.py   ← FastAPI dependency getter
├── scripts/
│   ├── download_data.py     ← Fetch dataset from UCI
│   └── train.py             ← Train and save Random Forest model
├── cli.py                   ← Typer CLI entry point
├── tests/
│   ├── test_extractor.py    ← Feature extraction tests (16)
│   ├── test_scorer.py       ← Model scoring tests (4)
│   ├── test_predict_route.py← API route tests (6)
│   ├── test_batch_route.py  ← Batch prediction tests (2)
│   ├── test_health.py       ← Health endpoint tests (2)
│   ├── test_cli.py          ← CLI tests (6)
│   └── fixtures/urls.py     ← Test URL datasets
├── requirements.txt
├── .env.example
└── README.md
```

## Running Tests

```bash
pytest tests/ -v
```

## Tech Stack

| Layer | Library |
|---|---|
| API | FastAPI 0.115.x |
| Server | Uvicorn 0.30.x |
| ML | scikit-learn 1.5.x (Random Forest) |
| Data | pandas, numpy |
| URL parsing | tldextract |
| Explainability | SHAP (TreeExplainer) |
| CLI | Typer |
| Validation | Pydantic v2 |
| Testing | pytest + httpx |
