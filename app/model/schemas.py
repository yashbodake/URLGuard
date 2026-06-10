"""Pydantic schemas for model predictions and metadata."""

from datetime import datetime

from pydantic import BaseModel, Field


class FeatureContributionSchema(BaseModel):
    """A single feature's SHAP contribution to a prediction."""

    feature: str
    shap_value: float
    direction: str = Field(description="phishing or legitimate")


class PredictResultSchema(BaseModel):
    """Full prediction result for a single URL."""

    url: str
    label: str = Field(description="PHISHING or LEGITIMATE")
    risk_score: float = Field(ge=0.0, le=1.0)
    confidence: str = Field(description="HIGH, MEDIUM, or LOW")
    top_features: list[FeatureContributionSchema]
    features: dict[str, float]
    processing_ms: float


class PredictRequestSchema(BaseModel):
    """Request body for single URL prediction."""

    url: str


class BatchPredictRequestSchema(BaseModel):
    """Request body for batch URL prediction."""

    urls: list[str]


class BatchPredictResultSchema(BaseModel):
    """Batch prediction response."""

    results: list[PredictResultSchema]
    summary: dict


class ModelInfoSchema(BaseModel):
    """Model metadata and performance metrics."""

    algorithm: str
    n_estimators: int
    trained_at: str
    dataset_size: int
    threshold: float
    feature_count: int
    feature_names: list[str]
    metrics: dict[str, float]


class HealthSchema(BaseModel):
    """Health check response."""

    status: str
    model_loaded: bool
    uptime_seconds: float


class ErrorSchema(BaseModel):
    """Standard error response."""

    error: str
    detail: str
    timestamp: str
