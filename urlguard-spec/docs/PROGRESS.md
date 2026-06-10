# Progress Tracker — URLGuard

> **AGENT INSTRUCTION**: Update this file as you complete tasks. Change `[ ]` to `[x]`.
> Add notes under tasks if you made a different decision.
> This file is the shared state between all agents and sessions.

---

## Pre-Day 1 — Data Setup (do this first, before any code)
- [ ] Download PhiUSIIL dataset from UCI: https://archive.ics.uci.edu/dataset/967/phiusiil+phishing+url+dataset
  - Save to `data/raw/PhiUSIIL_Dataset.csv`
  - Verify columns: `URL` and `label` (1=phishing, 0=legitimate)
  - Check shape: should be ~235k rows
- [ ] If UCI download fails, use Kaggle alternative:
  - Search "Web page Phishing Detection Dataset" on Kaggle
  - Download and save to `data/raw/`
  - Adjust column names in `scripts/train.py` accordingly
- [ ] Add `data/raw/`, `data/processed/`, `data/model/` to `.gitignore`

---

## Day 1 — Feature Engineering
**Goal**: Feature extractor working, all 15 features correct, unit tests passing

### Setup
- [ ] Create `requirements.txt` with pinned versions
- [ ] Create `.env.example`
- [ ] Create `app/config.py` using pydantic-settings
- [ ] Create `app/main.py` — FastAPI app, startup event, router registration

### Feature Layer
- [ ] Create `app/features/constants.py`
  - [ ] `SUSPICIOUS_TLDS` set
  - [ ] `BRAND_NAMES` set
  - [ ] `FEATURE_NAMES` list (ordered, 15 items, matching FEATURES.md)
- [ ] Create `app/features/extractor.py`
  - [ ] `extract_features(url: str) -> dict[str, float]`
  - [ ] All 15 features per FEATURES.md index order
  - [ ] Graceful handling of malformed URLs (return defaults, never raise)
  - [ ] `features_to_vector(features: dict) -> np.ndarray` — shape (1, 15)
- [ ] Create `app/features/validator.py`
  - [ ] `validate_url(url: str) -> bool` — basic scheme check (http/https)

### Tests — Day 1
- [ ] `tests/fixtures/urls.py` — dict of test URLs with expected feature values
  - [ ] Include: normal URL, phishing URL, IP-based URL, subdomain brand abuse, malformed URL
- [ ] `tests/test_extractor.py`
  - [ ] `url_length` correct for known URL
  - [ ] `has_ip_address` = 1 for `http://192.168.1.1/login`
  - [ ] `tld_is_suspicious` = 1 for `.xyz` domain
  - [ ] `has_brand_in_subdomain` = 1 for `paypal.evil.com`
  - [ ] `has_brand_in_subdomain` = 0 for `paypal.com` (brand IS the domain)
  - [ ] Malformed URL returns dict with all defaults, no exception
  - [ ] `features_to_vector` returns shape `(1, 15)` with dtype float64

### Day 1 Done When:
- `extract_features("https://paypal-security-update.xyz/login")` returns correct dict
- All Day 1 tests pass
- No network calls made during any test

---

## Day 2 — Model Training & Scoring
**Goal**: Model trained, evaluated, saved, scoring endpoint working

### Training Script
- [ ] Create `scripts/download_data.py` — downloads PhiUSIIL from UCI
- [ ] Create `scripts/train.py`
  - [ ] Load CSV from `data/raw/`
  - [ ] Apply `extract_features()` to every URL (use `df.apply()` with progress bar via `tqdm`)
  - [ ] Build feature matrix (N × 15) and label vector
  - [ ] 80/20 stratified train/test split (`stratify=y, random_state=42`)
  - [ ] Train `RandomForestClassifier(n_estimators=200, max_depth=20, class_weight='balanced', random_state=42, n_jobs=-1)`
  - [ ] Evaluate on test set: accuracy, F1, precision, recall, ROC-AUC, confusion matrix
  - [ ] Print evaluation report to console
  - [ ] Verify targets met: F1 > 0.93, Recall > 0.95 before saving
  - [ ] Save model artifact to `data/model/rf_model.joblib`

### Model Layer
- [ ] Create `app/model/schemas.py`
  - [ ] `FeatureContribution` — feature, shap_value, direction
  - [ ] `PredictResult` — url, label, risk_score, confidence, top_features, features, processing_ms
  - [ ] `ModelInfo` — algorithm, metrics, trained_at, etc.
- [ ] Create `app/model/scorer.py`
  - [ ] Module-level singleton: `_model_artifact: dict | None = None`
  - [ ] `load_model(path: str) -> bool`
  - [ ] `is_loaded() -> bool`
  - [ ] `score_url(url: str) -> PredictResult` — full pipeline: validate → extract → predict → explain
- [ ] Create `app/model/explainer.py`
  - [ ] `init_explainer(model)` — creates SHAP TreeExplainer singleton
  - [ ] `get_top_features(feature_vector, feature_names, n=5) -> list[FeatureContribution]`
- [ ] Wire `load_model()` + `init_explainer()` into FastAPI startup event

### API Layer
- [ ] Create `app/api/dependencies.py` — `get_scorer()` FastAPI dependency
- [ ] Create `app/api/router_predict.py`
  - [ ] `POST /predict`
  - [ ] `POST /predict/batch`
- [ ] Create `app/api/router_model.py`
  - [ ] `GET /model/info`
  - [ ] `GET /health`

### Tests — Day 2
- [ ] `tests/test_scorer.py`
  - [ ] `score_url` returns correct label for known phishing URL
  - [ ] `score_url` returns correct label for known legitimate URL
  - [ ] `risk_score` is in [0.0, 1.0]
  - [ ] `top_features` has exactly 5 items
- [ ] `tests/test_predict_route.py`
  - [ ] `/predict` returns 200 with label, score, features
  - [ ] `/predict` with no model returns 503
  - [ ] `/predict` with invalid URL returns 422
  - [ ] `/predict/batch` with 101 URLs returns 413

### Day 2 Done When:
- `python scripts/train.py` completes with F1 > 0.93 and saves model
- `POST /predict` returns label, score, top_features, all_features
- Evaluation metrics printed and targets met

---

## Day 3 — CLI + Polish
**Goal**: CLI working, tests complete, README done

### CLI
- [ ] Create `cli.py` using Typer
  - [ ] `python cli.py <url>` — score a single URL
  - [ ] Coloured output: red header for PHISHING, green for LEGITIMATE
  - [ ] Show: URL, label, score, confidence, top-5 features with SHAP values
  - [ ] Exit code 1 = PHISHING, exit code 0 = LEGITIMATE
  - [ ] `python cli.py --help` works

### Tests — Day 3
- [ ] `tests/test_cli.py` — CLI returns exit code 1 for known phishing, 0 for legitimate
- [ ] `tests/test_batch_route.py` — 3 URLs batch returns 3 results in order
- [ ] `tests/test_health.py` — `/health` returns `model_loaded: true`

### Polish
- [ ] Create `tests/fixtures/urls.py` with at least 10 known phishing + 10 legitimate test URLs
- [ ] Update `README.md` — setup, data download, training, API usage, CLI usage
- [ ] Verify full demo flow: download data → train → start server → POST /predict → CLI

### Day 3 Done When:
- `python cli.py "http://paypal.verify.tk/login"` prints PHISHING in red, exits with code 1
- `python cli.py "https://www.google.com"` prints LEGITIMATE in green, exits with code 0
- All tests pass
- README has full setup instructions

---

## Implementation Notes
> Add notes here as you go

- (empty — fill in as you build)

---

## Final Checklist
- [ ] All Day 1, 2, 3 tasks checked off
- [ ] `pytest tests/ -v` passes with 0 failures
- [ ] `python scripts/train.py` runs cleanly and meets F1 > 0.93
- [ ] `python cli.py <url>` works offline
- [ ] No data files or model files committed to git
- [ ] README complete with demo instructions
