# Product Requirements Document — URLGuard

## 1. Overview
URLGuard is a phishing URL classifier that extracts 15 structural and lexical
features from a URL string and uses a trained Random Forest to classify it as
phishing or legitimate, returning a risk score and feature importance breakdown.

**Timeline**: 3 working days
**Audience**: Portfolio / technical interview showcase
**Primary value**: End-to-end supervised ML pipeline — data → features → train →
evaluate → serve — with explainability (SHAP) and two delivery surfaces (API + CLI)

---

## 2. Goals
- G1: Extract 15 features from any URL string with zero network calls
- G2: Train a Random Forest on PhiUSIIL dataset (~235k URLs) and achieve F1 > 0.93
- G3: Optimise for low false negatives (missing phishing is worse than false alarms)
- G4: Return a risk score [0.0–1.0] with a PHISHING / LEGITIMATE label
- G5: Return top-5 feature contributions (SHAP values) explaining the prediction
- G6: Expose scoring via both a FastAPI endpoint and a CLI tool

## 3. Non-Goals
- No real-time PhishTank feed integration
- No URL fetching or DOM/HTML analysis (URL features only)
- No browser extension
- No model retraining API endpoint (train offline via script)
- No user authentication
- No bulk dataset upload endpoint

---

## 4. User Stories

### US-01: Score a URL via API
As a developer, I want to POST a URL and get back a risk score, label, and
feature breakdown so I can integrate it into a security pipeline.

**Acceptance**:
- POST `/predict` accepts `{"url": "https://..."}`
- Returns score, label, top-5 SHAP features, all 15 raw feature values
- Response time < 100ms per URL (feature extraction is fast, no I/O)

### US-02: Score a URL via CLI
As a developer, I want to run `python cli.py <url>` from a terminal and see
a formatted risk assessment so I can quickly check suspicious URLs.

**Acceptance**:
- `python cli.py "https://paypal-security-update.xyz/login"` prints a clean report
- Shows: URL, label (colour-coded), risk score, top-5 features with values
- Exit code 1 if PHISHING, exit code 0 if LEGITIMATE (pipeable)

### US-03: Batch score multiple URLs
As a developer, I want to POST a list of URLs and get back all results so I
can check a set of links at once.

**Acceptance**:
- POST `/predict/batch` accepts array of up to 100 URLs
- Returns array of results in same order
- Response time < 2 seconds for 100 URLs

### US-04: Check model info
As a developer, I want to GET model metadata so I can confirm the model
version, training date, and performance metrics.

**Acceptance**:
- GET `/model/info` returns algorithm, training date, dataset size, F1 score,
  precision, recall, feature names

### US-05: Health check
**Acceptance**: GET `/health` returns model loaded status + uptime

---

## 5. Functional Requirements

### 5.1 Feature Extraction
- FR-1: Extract exactly the 15 features defined in `docs/FEATURES.md`
- FR-2: Feature extraction must be PURE — same URL always returns same features
- FR-3: No network calls, no DNS lookups, no HTTP requests during feature extraction
- FR-4: Handle malformed URLs gracefully — return default feature values, never crash
- FR-5: All features must be numerical (int or float) — no strings fed to model

### 5.2 Model Training
- FR-6: Algorithm: `sklearn.ensemble.RandomForestClassifier`
- FR-7: Hyperparameters: `n_estimators=200, max_depth=20, class_weight='balanced', random_state=42, n_jobs=-1`
- FR-8: `class_weight='balanced'` is mandatory — dataset is imbalanced (56% legit / 44% phish)
- FR-9: Evaluation must report: accuracy, precision, recall, F1, ROC-AUC, confusion matrix
- FR-10: Optimise threshold for recall (catch more phishing even at cost of false positives)
  - Default threshold: 0.4 (lower than 0.5 — biased toward catching phishing)
- FR-11: Save model artifact to `data/model/rf_model.joblib`
- FR-12: Model artifact must include: model, feature_names, threshold, metrics, trained_at

### 5.3 Scoring
- FR-13: Load model from disk at API startup
- FR-14: Score = `model.predict_proba(X)[0][1]` — probability of PHISHING class
- FR-15: Label = PHISHING if score >= threshold, else LEGITIMATE
- FR-16: SHAP TreeExplainer computes top-5 feature contributions per prediction
- FR-17: Return both the score AND the raw feature values in the response

### 5.4 Evaluation targets (must meet before calling Day 2 done)
| Metric | Target |
|---|---|
| F1 Score | > 0.93 |
| Recall (phishing) | > 0.95 |
| Precision (phishing) | > 0.90 |
| ROC-AUC | > 0.97 |

---

## 6. Non-Functional Requirements
- NFR-1: Single URL prediction < 100ms (p99) — feature extraction + inference only
- NFR-2: Batch of 100 URLs < 2 seconds
- NFR-3: Server must not crash on malformed or empty URLs — return 422 with details
- NFR-4: CLI must work offline (no internet required after model is trained)
- NFR-5: Test coverage > 75% for `app/features/` and `app/model/`

---

## 7. Error Handling Contract
```json
{
  "error": "SHORT_ERROR_CODE",
  "detail": "Human readable explanation",
  "timestamp": "2025-01-01T00:00:00Z"
}
```

| Code | HTTP | When |
|---|---|---|
| `MODEL_NOT_LOADED` | 503 | Scoring before model is loaded |
| `INVALID_URL` | 422 | URL fails basic format validation |
| `BATCH_TOO_LARGE` | 413 | > 100 URLs in batch |
| `EMPTY_URL` | 422 | Empty string submitted |
