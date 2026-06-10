# ML Conventions — URLGuard

## Model Singleton Pattern
```python
# app/model/scorer.py
_model_artifact: dict | None = None

def load_model(path: str) -> bool:
    global _model_artifact
    try:
        _model_artifact = joblib.load(path)
        return True
    except FileNotFoundError:
        logger.warning(f"Model not found at {path}. Run scripts/train.py first.")
        return False

def is_loaded() -> bool:
    return _model_artifact is not None
```

## Feature Vector Contract
- Always shape `(1, 15)` — never flat `(15,)`
- Dtype: `float64`
- Feature order: fixed per `FEATURE_NAMES` in `app/features/constants.py`
- Never feed string features to the model

## Training Script Conventions
```python
# Minimum viable training script structure
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score
import joblib
from datetime import datetime, timezone

df = pd.read_csv("data/raw/PhiUSIIL_Dataset.csv")
# Extract features — use tqdm for progress on 235k rows
from tqdm import tqdm
tqdm.pandas()
features_df = df["URL"].progress_apply(lambda url: pd.Series(extract_features(url)))
X = features_df[FEATURE_NAMES].values
y = df["label"].values  # 1=phishing, 0=legitimate

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

model = RandomForestClassifier(
    n_estimators=200,
    max_depth=20,
    class_weight="balanced",
    random_state=42,
    n_jobs=-1,  # use all CPU cores
)
model.fit(X_train, y_train)

# Always evaluate before saving
y_pred = model.predict(X_test)
y_proba = model.predict_proba(X_test)[:, 1]
print(classification_report(y_test, y_pred, target_names=["legitimate", "phishing"]))
print(f"ROC-AUC: {roc_auc_score(y_test, y_proba):.4f}")
```

## SHAP Usage
```python
import shap

# Init once at startup — NOT per request
explainer = shap.TreeExplainer(model)

# Per prediction
shap_values = explainer.shap_values(feature_vector)  # shape: [2, 1, 15]
phishing_shap = shap_values[1][0]  # index [1] = PHISHING class
```

## Threshold — Use 0.4, not 0.5
```python
risk_score = model.predict_proba(X)[0][1]  # prob of class 1 (phishing)
threshold = model_artifact["threshold"]    # 0.4 from artifact
label = "PHISHING" if risk_score >= threshold else "LEGITIMATE"
```

## Confidence Calculation
```python
def get_confidence(score: float, threshold: float) -> str:
    distance = abs(score - threshold)
    if distance > 0.35:
        return "HIGH"
    elif distance > 0.15:
        return "MEDIUM"
    else:
        return "LOW"
```
