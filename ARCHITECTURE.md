# Architecture — URLGuard

## 1. High-Level Data Flow

### Training Flow (offline, run once)
```
PhiUSIIL CSV
      │
      ▼
┌──────────────────┐
│ scripts/train.py │  Load CSV, call extract_features() on each URL
└────────┬─────────┘
         │  DataFrame (N × 15)
         ▼
┌──────────────────┐
│ Train/Test Split │  80/20 stratified split
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ RandomForest.fit │  n_estimators=200, class_weight='balanced'
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Evaluate         │  F1, Recall, Precision, ROC-AUC, confusion matrix
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Save artifact    │  joblib → data/model/rf_model.joblib
└──────────────────┘
```

### Inference Flow (real-time, API + CLI)
```
URL string
      │
      ▼
┌──────────────────┐
│ Feature extractor│  app/features/extractor.py — pure, no I/O
│ (15 features)    │
└────────┬─────────┘
         │  np.ndarray (1 × 15)
         ▼
┌──────────────────┐
│ model.predict_   │  app/model/scorer.py
│ proba(X)         │  Returns probability of PHISHING class
└────────┬─────────┘
         │  raw score [0.0–1.0]
         ▼
┌──────────────────┐
│ Threshold check  │  score >= 0.4 → PHISHING, else LEGITIMATE
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ SHAP explainer   │  app/model/explainer.py
│ Top-5 features   │  TreeExplainer.shap_values()
└────────┬─────────┘
         │
         ▼
     PredictResult
```

---

## 2. Module Breakdown

### `app/features/`
| File | Responsibility |
|---|---|
| `extractor.py` | `extract_features(url: str) -> dict[str, float]` — the core pure function |
| `constants.py` | `SUSPICIOUS_TLDS`, `BRAND_NAMES`, `FEATURE_NAMES` — single source of truth |
| `validator.py` | Basic URL format validation before extraction |

### `app/model/`
| File | Responsibility |
|---|---|
| `scorer.py` | Module-level singleton. `load_model()`, `score_url(url) -> PredictResult` |
| `explainer.py` | SHAP `TreeExplainer` singleton. `get_top_features(X, n=5) -> list[FeatureContribution]` |
| `schemas.py` | `PredictResult`, `FeatureContribution`, `ModelInfo` dataclasses |

### `app/api/`
| File | Responsibility |
|---|---|
| `router_predict.py` | `POST /predict`, `POST /predict/batch` |
| `router_model.py` | `GET /model/info`, `GET /health` |
| `dependencies.py` | `get_scorer()` FastAPI dependency |

### `scripts/`
| File | Responsibility |
|---|---|
| `download_data.py` | Downloads PhiUSIIL dataset from UCI, saves to `data/raw/` |
| `train.py` | Full training pipeline — load, extract features, train, evaluate, save |

### `cli.py`
- Uses `typer` for CLI
- Calls the same `score_url()` from `app/model/scorer.py`
- Coloured output: red for PHISHING, green for LEGITIMATE (using `typer.style()`)
- Exit code 1 = PHISHING, 0 = LEGITIMATE

---

## 3. Model Choice Rationale — Why Random Forest over XGBoost/LogReg

| Criterion | Random Forest | XGBoost | Logistic Regression |
|---|---|---|---|
| Training speed on 235k rows | Fast (parallelisable) | Fast | Very fast |
| SHAP support | Native TreeExplainer | Native TreeExplainer | LinearExplainer (less informative) |
| Handles imbalanced data | Good with `class_weight='balanced'` | Good with `scale_pos_weight` | Needs careful tuning |
| Interpretability | Feature importance built in | Feature importance built in | Coefficients |
| Overfitting risk | Low (ensemble) | Moderate | Low |
| Portfolio story | "Classic, robust, explainable" | "Gradient boosting, state of art" | "Too simple for this" |

**Verdict**: Random Forest is the right default for a 3-day portfolio project — well understood,
SHAP-compatible, handles class imbalance cleanly, and gives great results on URL features.
If the interviewer asks "why not XGBoost?", the honest answer is: Random Forest is simpler
to explain, and on this feature set both models achieve similar F1. XGBoost is mentioned as
a potential upgrade.

---

## 4. Threshold Tuning — Why 0.4, Not 0.5

Standard `predict()` uses 0.5. We lower it to 0.4 because:
- **Asymmetric cost**: missing a phishing URL (false negative) is worse than flagging a
  legitimate URL (false positive). A user clicking a phishing link loses credentials;
  a legitimate URL incorrectly flagged is just inconvenient.
- Lowering threshold increases recall (catch more phishing) at slight cost to precision.
- 0.4 is configurable via `.env` — not hardcoded.

Threshold is stored in the model artifact so scoring behaviour is consistent.

---

## 5. SHAP Integration

```python
# app/model/explainer.py
import shap
import numpy as np

_explainer = None  # module-level singleton

def init_explainer(model) -> None:
    global _explainer
    _explainer = shap.TreeExplainer(model)

def get_top_features(
    feature_vector: np.ndarray,
    feature_names: list[str],
    n: int = 5
) -> list[dict]:
    """Return top-n features by absolute SHAP value for a single prediction."""
    shap_values = _explainer.shap_values(feature_vector)
    # shap_values[1] = SHAP values for PHISHING class
    values = shap_values[1][0]
    contributions = sorted(
        zip(feature_names, values),
        key=lambda x: abs(x[1]),
        reverse=True
    )[:n]
    return [
        {"feature": name, "shap_value": float(val), "direction": "phishing" if val > 0 else "legitimate"}
        for name, val in contributions
    ]
```

---

## 6. Model Artifact Schema
```python
{
    "model": RandomForestClassifier,   # trained model object
    "feature_names": list[str],        # ordered, matches FEATURES.md
    "threshold": float,                # default 0.4
    "trained_at": datetime,            # UTC
    "dataset_size": int,               # total training samples
    "metrics": {
        "accuracy": float,
        "f1": float,
        "precision": float,
        "recall": float,
        "roc_auc": float,
    }
}
```

---

## 7. Configuration via .env
```env
MODEL_PATH=data/model/rf_model.joblib
RISK_THRESHOLD=0.4
MAX_BATCH_SIZE=100
LOG_LEVEL=INFO
```

---

## 8. Dataset Note

**PhiUSIIL** (recommended):
- 134,850 legitimate + 100,945 phishing = ~236k URLs
- Label column: `label` (1 = phishing, 0 = legitimate)
- URL column: `URL`
- Source: UCI ML Repository, free to download

**Alternative if PhiUSIIL download fails**:
Kaggle "Web page Phishing Detection Dataset"
- ~11k URLs, 87 pre-extracted features (can use a subset)
- Search on Kaggle: "web-page-phishing-detection-dataset"

**IMPORTANT**: Do NOT commit the dataset to git. It is 50MB+.
Add `data/raw/` and `data/processed/` to `.gitignore`.
