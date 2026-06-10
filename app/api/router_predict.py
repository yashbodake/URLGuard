"""Prediction API routes — POST /predict and POST /predict/batch."""

import logging
import time
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from app.model import scorer
from app.model.schemas import (
    BatchPredictRequestSchema,
    BatchPredictResultSchema,
    ErrorSchema,
    PredictRequestSchema,
    PredictResultSchema,
)
from app.api.dependencies import get_scorer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/predict", tags=["prediction"])


@router.post(
    "",
    response_model=PredictResultSchema,
    responses={
        422: {"model": ErrorSchema},
        503: {"model": ErrorSchema},
    },
)
def predict(
    request: PredictRequestSchema,
    s: scorer = Depends(get_scorer),
) -> PredictResultSchema:
    """Score a single URL and return risk assessment with SHAP explanations."""
    if not s.is_loaded():
        raise HTTPException(
            status_code=503,
            detail=ErrorSchema(
                error="MODEL_NOT_LOADED",
                detail="Model not found. Run scripts/train.py first.",
                timestamp=datetime.now(timezone.utc).isoformat(),
            ).model_dump(),
        )

    if not request.url or not request.url.strip():
        raise HTTPException(
            status_code=422,
            detail=ErrorSchema(
                error="EMPTY_URL",
                detail="URL cannot be empty.",
                timestamp=datetime.now(timezone.utc).isoformat(),
            ).model_dump(),
        )

    if not request.url.startswith(("http://", "https://")):
        raise HTTPException(
            status_code=422,
            detail=ErrorSchema(
                error="INVALID_URL",
                detail="URL must start with http:// or https://",
                timestamp=datetime.now(timezone.utc).isoformat(),
            ).model_dump(),
        )

    return s.score_url(request.url)


@router.post(
    "/batch",
    response_model=BatchPredictResultSchema,
    responses={
        413: {"model": ErrorSchema},
        503: {"model": ErrorSchema},
    },
)
def predict_batch(
    request: BatchPredictRequestSchema,
    s: scorer = Depends(get_scorer),
) -> BatchPredictResultSchema:
    """Score multiple URLs at once. Max 100."""
    if not s.is_loaded():
        raise HTTPException(
            status_code=503,
            detail=ErrorSchema(
                error="MODEL_NOT_LOADED",
                detail="Model not found. Run scripts/train.py first.",
                timestamp=datetime.now(timezone.utc).isoformat(),
            ).model_dump(),
        )

    # Manual validation for > 100 URLs to return 413
    if len(request.urls) > 100:
        raise HTTPException(
            status_code=413,
            detail=ErrorSchema(
                error="BATCH_TOO_LARGE",
                detail="Maximum 100 URLs per batch request.",
                timestamp=datetime.now(timezone.utc).isoformat(),
            ).model_dump(),
        )

    start = time.perf_counter()
    results = []
    phishing_count = 0
    legitimate_count = 0

    for url in request.urls:
        if not url.startswith(("http://", "https://")):
            continue
        result = s.score_url(url)
        results.append(result)
        if result.label == "PHISHING":
            phishing_count += 1
        else:
            legitimate_count += 1

    elapsed_ms = (time.perf_counter() - start) * 1000

    return BatchPredictResultSchema(
        results=results,
        summary={
            "total": len(results),
            "phishing_count": phishing_count,
            "legitimate_count": legitimate_count,
            "processing_ms": round(elapsed_ms, 2),
        },
    )
