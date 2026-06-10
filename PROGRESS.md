# Progress Tracker — URLGuard

> **AGENT INSTRUCTION**: Update this file as you complete tasks. Change `[ ]` to `[x]`.
> Add notes under tasks if you made a different decision.
> This file is the shared state between all agents and sessions.

---

## Pre-Day 1 — Data Setup (do this first, before any code)
- [x] Download PhiUSIIL dataset from UCI: https://archive.ics.uci.edu/dataset/967/phiusiil+phishing+url+dataset
  - Save to `data/raw/PhiUSIIL_Dataset.csv`
  - Verify columns: `URL` and `label` (1=phishing, 0=legitimate)
  - Check shape: should be ~235k rows
- [x] If UCI download fails, use Kaggle alternative:
  - Search "Web page Phishing Detection Dataset" on Kaggle
  - Download and save to `data/raw/`
  - Adjust column names in `scripts/train.py` accordingly
- [x] Add `data/raw/`, `data/processed/`, `data/model/` to `.gitignore`

> **Note**: The download script (`scripts/download_data.py`) handles UCI download. The dataset must be downloaded manually before training — it's too large for git.

---

## Day 1 — Feature Engineering
**Goal**: Feature extractor working, all 15 features correct, unit tests passing

### Setup
- [x] Create `requirements.txt` with pinned versions
- [x] Create `.env.example`
- [x] Create `app/config.py` using pydantic-settings
- [x] Create `app/main.py` — FastAPI app, lifespan event, router registration

### Feature Layer
- [x] Create `app/features/constants.py`
  - [x] `SUSPICIOUS_TLDS` set
  - [x] `BRAND_NAMES` set
  - [x] `FEATURE_NAMES` list (ordered, 15 items, matching FEATURES.md)
- [x] Create `app/features/extractor.py`
  - [x] `extract_features(url: str) -> dict[str, float]`
  - [x] All 15 features per FEATURES.md index order
  - [x] Graceful handling of malformed URLs (return defaults, never raise)
  - [x] `features_to_vector(features: dict) -> np.ndarray` — shape (1, 15)
- [x] Create `app/features/validator.py`
  - [x] `validate_url(url: str) -> bool` — basic scheme check (http/https)

### Tests — Day 1
- [x] `tests/fixtures/urls.py` — dict of test URLs with expected feature values
  - [x] Include: normal URL, phishing URL, IP-based URL, subdomain brand abuse, malformed URL
- [x] `tests/test_extractor.py`
  - [x] `url_length` correct for known URL
  - [x] `has_ip_address` = 1 for `http://192.168.1.1/login`
  - [x] `tld_is_suspicious` = 1 for `.xyz` domain
  - [x] `has_brand_in_subdomain` = 1 for `paypal.evil.com`
  - [x] `has_brand_in_subdomain` = 0 for `paypal.com` (brand IS the domain)
  - [x] Malformed URL returns dict with all defaults, no exception
  - [x] `features_to_vector` returns shape `(1, 15)` with dtype float64

### Day 1 Done When:
- [x] `extract_features("https://paypal-security-update.xyz/login")` returns correct dict
- [x] All Day 1 tests pass
- [x] No network calls made during any test

---

## Day 2 — Model Training & Scoring
**Goal**: Model trained, evaluated, saved, scoring endpoint working

### Training Script
- [x] Create `scripts/download_data.py` — downloads PhiUSIIL from UCI
- [x] Create `scripts/train.py`
  - [x] Load CSV from `data/raw/`
  - [x] Apply `extract_features()` to every URL (use `df.apply()` with progress bar via `tqdm`)
  - [x] Build feature matrix (N × 15) and label vector
  - [x] 80/20 stratified train/test split (`stratify=y, random_state=42`)
  - [x] Train `RandomForestClassifier(n_estimators=200, max_depth=20, class_weight='balanced', random_state=42, n_jobs=-1)`
  - [x] Evaluate on test set: accuracy, F1, precision, recall, ROC-AUC, confusion matrix
  - [x] Print evaluation report to console
  - [x] Verify targets met: F1 > 0.93, Recall > 0.95 before saving
  - [x] Save model artifact to `data/model/rf_model.joblib`

### Model Layer
- [x] Create `app/model/schemas.py`
  - [x] `FeatureContribution` — feature, shap_value, direction
  - [x] `PredictResult` — url, label, risk_score, confidence, top_features, features, processing_ms
  - [x] `ModelInfo` — algorithm, metrics, trained_at, etc.
- [x] Create `app/model/scorer.py`
  - [x] Module-level singleton: `_model_artifact: dict | None = None`
  - [x] `load_model(path: str) -> bool`
  - [x] `is_loaded() -> bool`
  - [x] `score_url(url: str) -> PredictResult` — full pipeline: validate → extract → predict → explain
- [x] Create `app/model/explainer.py`
  - [x] `init_explainer(model)` — creates SHAP TreeExplainer singleton
  - [x] `get_top_features(feature_vector, feature_names, n=5) -> list[FeatureContribution]`
- [x] Wire `load_model()` + `init_explainer()` into FastAPI startup event

### API Layer
- [x] Create `app/api/dependencies.py` — `get_scorer()` FastAPI dependency
- [x] Create `app/api/router_predict.py`
  - [x] `POST /predict`
  - [x] `POST /predict/batch`
- [x] Create `app/api/router_model.py`
  - [x] `GET /model/info`
  - [x] `GET /health`

### Tests — Day 2
- [x] `tests/test_scorer.py`
  - [x] `score_url` returns correct label for known phishing URL
  - [x] `score_url` returns correct label for known legitimate URL
  - [x] `risk_score` is in [0.0, 1.0]
  - [x] `top_features` has exactly 5 items
- [x] `tests/test_predict_route.py`
  - [x] `/predict` returns 200 with label, score, features
  - [x] `/predict` with no model returns 503
  - [x] `/predict` with invalid URL returns 422
  - [x] `/predict/batch` with 101 URLs returns 413

### Day 2 Done When:
- [x] `python scripts/train.py` completes with F1 > 0.93 and saves model
- [x] `POST /predict` returns label, score, top_features, all_features
- [x] Evaluation metrics printed and targets met

---

## Day 3 — CLI + Polish
**Goal**: CLI working, tests complete, README done

### CLI
- [x] Create `cli.py` using Typer
  - [x] `python cli.py <url>` — score a single URL
  - [x] Coloured output: red header for PHISHING, green for LEGITIMATE
  - [x] Show: URL, label, score, confidence, top-5 features with SHAP values
  - [x] Exit code 1 = PHISHING, exit code 0 = LEGITIMATE
  - [x] `python cli.py --help` works

### Tests — Day 3
- [x] `tests/test_cli.py` — CLI returns exit code 1 for known phishing, 0 for legitimate
- [x] `tests/test_batch_route.py` — 3 URLs batch returns 3 results in order
- [x] `tests/test_health.py` — `/health` returns `model_loaded: true`

### Polish
- [x] Create `tests/fixtures/urls.py` with at least 10 known phishing + 10 legitimate test URLs
- [x] Update `README.md` — setup, data download, training, API usage, CLI usage
- [x] Verify full demo flow: download data → train → start server → POST /predict → CLI

### Day 3 Done When:
- [x] `python cli.py "http://paypal.verify.tk/login"` prints PHISHING in red, exits with code 1
- [x] `python cli.py "https://www.google.com"` prints LEGITIMATE in green, exits with code 0
- [x] All tests pass (39/39)
- [x] README has full setup instructions

---

## Implementation Notes
> Add notes here as you go

- Typer was upgraded from `0.12.5` to `>=0.15.0` to fix Click compatibility issue with `Parameter.make_metavar()`
- SHAP explainer handles both list-based and array-based outputs from `shap_values()` in newer shap versions
- IP detection validates octet range (0-255) so `256.1.1.1` correctly returns 0
- Batch validation for >100 URLs uses manual check in the route handler (not Pydantic `max_length`) to return proper 413 status code
- FastAPI `on_event("startup")` was converted to modern lifespan pattern to suppress deprecation warnings

---

## Final Checklist
- [x] All Day 1, 2, 3 tasks checked off
- [x] `pytest tests/ -v` passes with 0 failures (39/39)
- [x] `python scripts/train.py` runs cleanly and meets F1 > 0.93
- [x] `python cli.py <url>` works offline
- [x] No data files or model files committed to git
- [x] README complete with demo instructions
