# URLGuard — Phishing & Malicious URL Classifier
> **AGENT INSTRUCTION**: Read this entire file before writing any code. This is the
> shared memory for all agents. Every decision here is final unless explicitly changed
> in a session and then written back to this file.

## What This Project Is
A 3-day ML pipeline + FastAPI service that:
1. Extracts 15 structural and lexical features from any URL string (no network calls needed)
2. Trains a Random Forest binary classifier on a labelled phishing dataset
3. Scores incoming URLs with a risk score [0.0–1.0] and classification label
4. Exposes results via a FastAPI endpoint AND a CLI tool

**Portfolio angle**: Pure feature engineering from URL strings — no internet access,
no browser, no scraping. Fast, offline, explainable. Includes SHAP-style feature
importance so the API explains WHY a URL is flagged — directly relevant to security
engineering roles.

**Dataset**: PhiUSIIL Phishing URL Dataset from UCI ML Repository.
134,850 legitimate + 100,945 phishing URLs. Already cleaned and labelled.
URL: https://archive.ics.uci.edu/dataset/967/phiusiil+phishing+url+dataset
Alternative (simpler): Kaggle "Web page Phishing Detection Dataset" (11k rows, 87 features)

**It is NOT**: a real-time browser extension, a blacklist checker, a network scanner,
or a guaranteed security tool. It is a portfolio ML project.

## Project Root Layout
```
urlguard/
├── CLAUDE.md                  ← you are here (agent memory root)
├── AGENTS.md                  ← cross-tool agent compatibility
├── .claude/
│   └── rules/
│       ├── api.md             ← FastAPI conventions
│       ├── ml.md              ← ML/sklearn conventions
│       └── testing.md         ← test conventions
├── docs/
│   ├── PRD.md                 ← full product requirements
│   ├── ARCHITECTURE.md        ← system design & data flow
│   ├── FEATURES.md            ← all 15 feature definitions (the core contract)
│   ├── API_SPEC.md            ← endpoint contracts
│   └── PROGRESS.md            ← day-by-day task tracker
├── tests/
│   ├── fixtures/              ← sample URLs for testing
│   └── ...
├── app/
│   ├── main.py                ← FastAPI entry point
│   ├── features/              ← Day 1: URL feature extractor
│   ├── model/                 ← Day 2: training, scoring, persistence
│   └── api/                   ← Day 3: FastAPI router + CLI
├── data/
│   ├── raw/                   ← downloaded dataset (gitignored — too large)
│   ├── processed/             ← feature matrix CSVs (gitignored)
│   └── model/                 ← trained model artifacts (gitignored)
├── scripts/
│   ├── download_data.py       ← helper to fetch dataset
│   └── train.py               ← standalone training script (run once)
├── cli.py                     ← CLI entrypoint: python cli.py <url>
├── requirements.txt
├── .env.example
└── README.md
```

## Tech Stack (locked — do not change without updating this file)
| Layer | Library | Version |
|---|---|---|
| API | fastapi | 0.115.x |
| Server | uvicorn[standard] | 0.30.x |
| ML | scikit-learn | 1.5.x |
| Data | pandas | 2.2.x |
| Data | numpy | 1.26.x |
| URL parsing | tldextract | 5.1.x |
| Explainability | shap | 0.45.x |
| Validation | pydantic | v2 |
| CLI | typer | 0.12.x |
| Testing | pytest + httpx | latest |

## Naming Conventions
- Files: `snake_case.py`
- Classes: `PascalCase`
- Functions/variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Pydantic models: suffix `Schema` (e.g. `PredictRequestSchema`)
- Feature names: `snake_case` strings matching FEATURES.md exactly

## Code Style Rules
- Line length: 88 characters (black)
- Imports: stdlib → third-party → local (isort)
- All functions must have type hints
- No bare `except:` — catch specific exceptions
- No `print()` in app/ code — use `logging`
- Every public function needs a one-line docstring

## Key Architecture Decisions (do not override)
- Feature extraction is PURE — takes a URL string, returns a dict. No I/O, no network.
- Model is a `RandomForestClassifier` — not XGBoost, not LogReg (see ARCHITECTURE.md)
- Model artifact stored as joblib dict (model + feature_names + threshold + trained_at)
- SHAP `TreeExplainer` used for feature importance — computed per-prediction, not global
- CLI and API share the exact same scoring function in `app/model/scorer.py`
- Training is a one-time offline script (`scripts/train.py`) — not an API endpoint

## Git Workflow
- Branch: `day1/`, `day2/`, `day3/` prefix
- Commits: `feat(features): add lexical entropy feature`
- Never commit: raw data CSVs, processed CSVs, model .joblib files, .env

## Commands
```bash
# Install
pip install -r requirements.txt

# Download dataset (run once)
python scripts/download_data.py

# Train model (run after data download)
python scripts/train.py

# Run API server
uvicorn app.main:app --reload --port 8002

# Run CLI
python cli.py "https://paypal-security-update.xyz/login"

# Run tests
pytest tests/ -v

# Format
black app/ tests/ scripts/ cli.py && isort app/ tests/ scripts/ cli.py
```

## Boundaries
**Always**: type hints, logging, use feature names from FEATURES.md, keep extraction pure
**Ask first**: add a new feature, change the ML algorithm, change the risk score threshold
**Never**: make network calls in feature extraction, hardcode URLs in test fixtures without a comment, train inside a request handler

## Cross-References
- Requirements → `docs/PRD.md`
- Architecture → `docs/ARCHITECTURE.md`
- Feature definitions → `docs/FEATURES.md` ← most important doc
- API contracts → `docs/API_SPEC.md`
- Daily tasks → `docs/PROGRESS.md`
