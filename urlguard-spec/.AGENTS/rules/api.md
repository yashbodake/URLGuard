# FastAPI Conventions — URLGuard

## Error Raising
```python
from datetime import datetime, timezone
from fastapi import HTTPException

def raise_api_error(status_code: int, error: str, detail: str):
    raise HTTPException(
        status_code=status_code,
        detail={"error": error, "detail": detail,
                "timestamp": datetime.now(timezone.utc).isoformat()}
    )
```

## URL Validation in Routes
```python
from app.features.validator import validate_url

if not url.strip():
    raise_api_error(422, "EMPTY_URL", "URL cannot be empty.")
if not validate_url(url):
    raise_api_error(422, "INVALID_URL", "URL must start with http:// or https://")
```

## Model Dependency
```python
# app/api/dependencies.py
def get_scorer():
    if not scorer.is_loaded():
        raise_api_error(503, "MODEL_NOT_LOADED",
                        "Model not found. Run: python scripts/train.py")
    return scorer
```
