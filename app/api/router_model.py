"""Model info and health API routes."""

import logging
import time
from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from app.model import scorer
from app.api.dependencies import get_scorer
from app.model.schemas import HealthSchema, ModelInfoSchema

logger = logging.getLogger(__name__)

router = APIRouter(tags=["model"])

START_TIME = time.time()


@router.get("/model/info", response_model=ModelInfoSchema)
def model_info(s: scorer = Depends(get_scorer)) -> ModelInfoSchema:
    """Return model metadata and performance metrics."""
    artifact = s.get_artifact()

    if artifact is None:
        return ModelInfoSchema(
            algorithm="unknown",
            n_estimators=0,
            trained_at="never",
            dataset_size=0,
            threshold=0.4,
            feature_count=0,
            feature_names=[],
            metrics={},
        )

    model = artifact["model"]
    return ModelInfoSchema(
        algorithm=type(model).__name__,
        n_estimators=model.n_estimators,
        trained_at=artifact.get("trained_at", "unknown"),
        dataset_size=artifact.get("dataset_size", 0),
        threshold=artifact.get("threshold", 0.4),
        feature_count=len(artifact.get("feature_names", [])),
        feature_names=artifact.get("feature_names", []),
        metrics=artifact.get("metrics", {}),
    )


@router.get("/health", response_model=HealthSchema)
def health(s: scorer = Depends(get_scorer)) -> HealthSchema:
    """Return health status including model loaded state and uptime."""
    return HealthSchema(
        status="ok",
        model_loaded=s.is_loaded(),
        uptime_seconds=round(time.time() - START_TIME, 1),
    )
