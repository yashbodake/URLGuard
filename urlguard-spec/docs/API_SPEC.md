# API Specification — URLGuard

Base URL (local dev): `http://localhost:8002`
All bodies: `application/json`

---

## POST `/predict`
Score a single URL.

**Request**:
```json
{
  "url": "https://paypal-security-update.xyz/verify/account/login?token=abc123"
}
```

**Success — 200**:
```json
{
  "url": "https://paypal-security-update.xyz/verify/account/login?token=abc123",
  "label": "PHISHING",
  "risk_score": 0.87,
  "confidence": "HIGH",
  "top_features": [
    {"feature": "tld_is_suspicious", "shap_value": 0.31, "direction": "phishing"},
    {"feature": "num_hyphens",        "shap_value": 0.24, "direction": "phishing"},
    {"feature": "domain_length",      "shap_value": 0.18, "direction": "phishing"},
    {"feature": "has_https",          "shap_value": -0.08, "direction": "legitimate"},
    {"feature": "lexical_diversity",  "shap_value": 0.07, "direction": "phishing"}
  ],
  "features": {
    "url_length": 79,
    "domain_length": 24,
    "path_length": 27,
    "num_dots": 2,
    "num_hyphens": 2,
    "num_at_symbols": 0,
    "num_query_params": 1,
    "has_ip_address": 0,
    "has_https": 1,
    "tld_is_suspicious": 1,
    "subdomain_depth": 0,
    "path_depth": 3,
    "has_brand_in_subdomain": 0,
    "lexical_diversity": 0.51,
    "digit_ratio": 0.04
  },
  "processing_ms": 18
}
```

**Confidence levels**:
- `HIGH`: score > 0.75 or score < 0.25
- `MEDIUM`: score 0.5–0.75 or 0.25–0.5
- `LOW`: score 0.4–0.5 (near threshold)

**Error — 422 (invalid URL)**:
```json
{"error": "INVALID_URL", "detail": "URL must start with http:// or https://", "timestamp": "..."}
```

**Error — 503 (model not loaded)**:
```json
{"error": "MODEL_NOT_LOADED", "detail": "Model not found. Run scripts/train.py first.", "timestamp": "..."}
```

---

## POST `/predict/batch`
Score multiple URLs at once. Max 100.

**Request**:
```json
{
  "urls": [
    "https://www.google.com",
    "http://paypal.verify-account.tk/login",
    "https://amazon.com/products"
  ]
}
```

**Success — 200**:
```json
{
  "results": [
    {"url": "https://www.google.com", "label": "LEGITIMATE", "risk_score": 0.04, "confidence": "HIGH", "top_features": [...], "features": {...}},
    {"url": "http://paypal.verify-account.tk/login", "label": "PHISHING", "risk_score": 0.91, "confidence": "HIGH", "top_features": [...], "features": {...}},
    {"url": "https://amazon.com/products", "label": "LEGITIMATE", "risk_score": 0.06, "confidence": "HIGH", "top_features": [...], "features": {...}}
  ],
  "summary": {
    "total": 3,
    "phishing_count": 1,
    "legitimate_count": 2,
    "processing_ms": 42
  }
}
```

---

## GET `/model/info`
Returns model metadata and performance metrics.

**Success — 200**:
```json
{
  "algorithm": "RandomForestClassifier",
  "n_estimators": 200,
  "trained_at": "2024-10-10T09:00:00Z",
  "dataset_size": 188760,
  "threshold": 0.4,
  "feature_count": 15,
  "feature_names": ["url_length", "domain_length", ...],
  "metrics": {
    "accuracy": 0.961,
    "f1": 0.948,
    "precision": 0.932,
    "recall": 0.965,
    "roc_auc": 0.987
  }
}
```

---

## GET `/health`

**Success — 200**:
```json
{
  "status": "ok",
  "model_loaded": true,
  "uptime_seconds": 3210
}
```

---

## CLI Interface

```bash
# Basic usage
python cli.py "https://paypal-security-update.xyz/login"

# Output (PHISHING case — printed in red)
╔══════════════════════════════════════════════════╗
║  URLGuard Risk Assessment                        ║
╠══════════════════════════════════════════════════╣
║  URL:    https://paypal-security-update.xyz/...  ║
║  Label:  ⚠  PHISHING                            ║
║  Score:  0.87  (HIGH confidence)                 ║
╠══════════════════════════════════════════════════╣
║  Top contributing features:                      ║
║  + tld_is_suspicious    →  +0.31 (phishing)      ║
║  + num_hyphens          →  +0.24 (phishing)      ║
║  + domain_length        →  +0.18 (phishing)      ║
║  - has_https            →  -0.08 (legitimate)    ║
║  + lexical_diversity    →  +0.07 (phishing)      ║
╚══════════════════════════════════════════════════╝

# Legitimate URL output (printed in green)
╔══════════════════════════════════════════════════╗
║  URLGuard Risk Assessment                        ║
╠══════════════════════════════════════════════════╣
║  URL:    https://www.google.com/search?q=python  ║
║  Label:  ✓  LEGITIMATE                          ║
║  Score:  0.04  (HIGH confidence)                 ║
╚══════════════════════════════════════════════════╝

# Exit codes (pipeable)
# Exit 0 = LEGITIMATE
# Exit 1 = PHISHING
python cli.py "http://evil.tk/steal" && echo "safe" || echo "danger"
```

---

## OpenAPI
- Swagger UI: `http://localhost:8002/docs`
- ReDoc: `http://localhost:8002/redoc`
