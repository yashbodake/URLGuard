# URLGuard — Test Report

**Date**: 2026-06-11
**Python**: 3.13.12 | **pytest**: 8.3.4 | **Platform**: linux

---

## Summary

| Metric              | Value       |
|---------------------|-------------|
| Total Tests         | 38          |
| Passed              | 38          |
| Failed              | 0           |
| Skipped             | 0           |
| Errors              | 0           |
| Warnings            | 2 (non-code)|
| Execution Time      | 5.05s       |
| **Pass Rate**       | **100%**    |

---

## Model Under Test

| Property           | Value                                          |
|--------------------|------------------------------------------------|
| Algorithm          | RandomForestClassifier (200 trees, max_depth=20) |
| Dataset            | PhiUSIIL Phishing URL Dataset (235,795 URLs)   |
| Accuracy           | 0.9975                                         |
| F1 Score           | 0.9971                                         |
| Precision          | 0.9991                                         |
| Recall             | 0.9950                                         |
| ROC-AUC            | 0.9988                                         |
| Decision Threshold | 0.40                                           |

---

## Test Files Breakdown

### 1. `tests/test_extractor.py` — Feature Extraction (13 tests)

Validates the pure URL feature extractor (`app/features/extractor.py`).

| # | Test | Description |
|---|------|-------------|
| 1 | `test_has_ip_address_true` | Returns 1 for raw IPv4 address |
| 2 | `test_has_ip_address_false` | Returns 0 for hostname |
| 3 | `test_has_ip_address_invalid` | Returns 0 for out-of-range octets (256.x.x.x), partial IPs |
| 4 | `test_brand_in_subdomain_true` | Returns 1 when brand name appears in subdomain |
| 5 | `test_brand_in_subdomain_false` | Returns 0 when brand name is the domain itself |
| 6 | `test_brand_in_subdomain_no_subdomain` | Returns 0 when no subdomain exists |
| 7 | `test_url_length_normal` | URL length matches `len(url)` for a known URL |
| 8 | `test_tld_is_suspicious_xyz` | Flags `.xyz` as suspicious TLD |
| 9 | `test_tld_is_suspicious_com` | `.com` is NOT flagged as suspicious |
| 10 | `test_tld_is_suspicious_tk` | Flags `.tk` as suspicious TLD |
| 11 | `test_malformed_url_returns_defaults` | Malformed URL returns all-zero feature dict without raising |
| 12 | `test_empty_url_returns_defaults` | Empty string returns all-zero feature dict |
| 13 | `test_none_url_returns_defaults` | `None` input returns all-zero feature dict |
| 14 | `test_features_to_vector_shape` | Output vector shape is `(1, 15)` with `float64` dtype |

**Edge cases covered**: IP octet range validation (0–255), empty/None/malformed input graceful degradation, brand-in-subdomain vs brand-in-domain disambiguation.

---

### 2. `tests/test_scorer.py` — Model Scoring (5 tests)

Validates the scoring pipeline (`app/model/scorer.py`) with a dummy RandomForest.

| # | Test | Description |
|---|------|-------------|
| 1 | `test_is_loaded_false` | `is_loaded()` returns False when no model is loaded |
| 2 | `test_is_loaded_true` | `is_loaded()` returns True after loading a model |
| 3 | `test_score_url_returns_result` | `score_url()` returns a `PredictResultSchema` with all expected fields (url, label, risk_score, confidence, top_features, features) |
| 4 | `test_score_url_risk_score_range` | Risk score is always in [0.0, 1.0] for legitimate, phishing, and IP-based URLs |
| 5 | `test_score_url_top_features_count` | Top SHAP features count is exactly 5 |
| 6 | `test_score_url_processing_ms` | `processing_ms` is a positive number |

**Test strategy**: Each test resets scorer module state via `autouse` fixture, then loads a small 10-tree dummy RandomForest trained on random data. This avoids dependency on the real 20 MB model artifact.

---

### 3. `tests/test_predict_route.py` — Predict API Routes (5 tests)

Validates the FastAPI `/predict` endpoint via `TestClient`.

| # | Test | Description |
|---|------|-------------|
| 1 | `test_predict_no_model_returns_503` | POST `/predict` without a loaded model returns HTTP 503 |
| 2 | `test_predict_invalid_url_returns_422` | POST `/predict` with `"not-a-url"` returns HTTP 422 (validation error) |
| 3 | `test_predict_returns_200` | POST `/predict` with valid URL returns 200 + `label`, `risk_score`, `features` fields |
| 4 | `test_predict_batch_too_large_returns_413` | POST `/predict/batch` with 101 URLs returns HTTP 413 (payload too large) |
| 5 | `test_health_model_not_loaded` | GET `/health` shows `model_loaded=false` when no model is present |
| 6 | `test_health_model_loaded` | GET `/health` shows `model_loaded=true` after loading |

**HTTP status code coverage**: 200 (success), 422 (validation), 413 (batch limit), 503 (model unavailable).

---

### 4. `tests/test_batch_route.py` — Batch Prediction (2 tests)

Validates the `/predict/batch` endpoint.

| # | Test | Description |
|---|------|-------------|
| 1 | `test_batch_three_urls_returns_three_results` | 3 URLs submitted → 3 results returned in order, with `summary.total == 3` |
| 2 | `test_batch_returns_summary_with_counts` | Response includes `phishing_count` and `legitimate_count` that sum to total |

---

### 5. `tests/test_health.py` — Health Check (2 tests)

Validates the `/health` endpoint independently.

| # | Test | Description |
|---|------|-------------|
| 1 | `test_health_returns_model_loaded_false` | Without model: `model_loaded=false`, `status="ok"` |
| 2 | `test_health_returns_model_loaded_true` | With model: `model_loaded=true`, `uptime_seconds > 0` |

---

### 6. `tests/test_cli.py` — CLI (6 tests)

Validates the Typer CLI (`cli.py`) using `CliRunner`.

| # | Test | Description |
|---|------|-------------|
| 1 | `test_cli_help_succeeds` | `--help` flag exits with code 0 |
| 2 | `test_cli_no_url_shows_help` | No URL argument shows usage (exit 0) |
| 3 | `test_cli_invalid_url_exits_2` | Invalid URL format exits with code 2 |
| 4 | `test_cli_with_real_model_succeeds` | Real model on disk works — exit code 0 or 1 |
| 5 | `test_cli_phishing_url_exits_1` | Phishing URL exits with code 1 (uses dummy model) |
| 6 | `test_cli_legitimate_url_exits_0` | Legitimate URL exits with code 0 (uses dummy model) |

**Exit code contract**: `0` = LEGITIMATE, `1` = PHISHING, `2` = error.

**Note**: `test_cli_with_real_model_succeeds` relies on the real `data/model/rf_model.joblib` being present on disk. All other CLI tests use the in-memory dummy model.

---

## Test Architecture

```
tests/
├── __init__.py
├── test_extractor.py      ← Day 1: Pure feature extraction (13 tests)
├── test_scorer.py          ← Day 2: Model scoring + SHAP (5 tests)
├── test_predict_route.py   ← Day 3: FastAPI /predict routes (5 tests)
├── test_batch_route.py     ← Day 3: FastAPI /predict/batch route (2 tests)
├── test_health.py          ← Day 3: FastAPI /health route (2 tests)
└── test_cli.py             ← Day 3: Typer CLI (6 tests)
```

### Test Isolation Strategy

- **Scorer state reset**: Every test file uses an `autouse` fixture that sets `scorer._model = None` and `scorer._model_artifact = None` before and after each test, ensuring no cross-test contamination.
- **Dummy model**: API and CLI tests create a 10-tree RandomForest on random data (seed=42) instead of loading the real 200-tree, 20 MB model. This keeps tests fast (~5s total) and independent of filesystem state.
- **Real model test**: One CLI test (`test_cli_with_real_model_succeeds`) exercises the full end-to-end path with the actual trained model, verifying the artifact loads and scores correctly.

### Warnings (non-blocking)

1. **PydanticDeprecatedSince20**: Class-based `config` in a dependency — does not affect URLGuard code.
2. **RequestsDependencyWarning**: `urllib3`/`chardet` version mismatch in `requests` — irrelevant to URLGuard functionality.

---

## How to Run

```bash
# Full suite
pytest tests/ -v

# Single module
pytest tests/test_extractor.py -v

# With coverage
pytest tests/ --cov=app --cov-report=term-missing
```

---

## Coverage by Layer

| Layer | Module | Tests | Key Invariants |
|-------|--------|-------|----------------|
| Feature extraction | `app/features/extractor.py` | 14 | Pure function, graceful on bad input, 15 features, fixed shape |
| Model scoring | `app/model/scorer.py` | 5 | Risk score [0,1], 5 SHAP features, positive latency |
| API — predict | `app/api/router_predict.py` | 5 | 200/422/413/503 status codes, schema compliance |
| API — batch | `app/api/router_predict.py` | 2 | Order preserved, summary counts sum correctly |
| API — health | `app/api/router_model.py` | 2 | model_loaded flag, uptime counter |
| CLI | `cli.py` | 6 | Exit codes 0/1/2, help text, validation |
