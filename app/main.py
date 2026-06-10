"""URLGuard FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router_model import router as model_router
from app.api.router_predict import router as predict_router
from app.config import settings
from app.model import scorer

logging.basicConfig(level=getattr(logging, settings.log_level, logging.INFO))
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load model and initialize SHAP explainer on startup."""
    logger.info("Starting URLGuard API...")
    loaded = scorer.load_model()
    if loaded:
        logger.info("Model loaded successfully.")
    else:
        logger.warning(
            "Model not loaded — predictions will return 503. "
            "Run scripts/train.py to train and save the model."
        )
    yield


app = FastAPI(
    title="URLGuard",
    description="Phishing & Malicious URL Classifier API",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(predict_router)
app.include_router(model_router)
