"""Download the PhiUSIIL Phishing URL Dataset from UCI ML Repository."""

import logging
from pathlib import Path

import pandas as pd
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATA_DIR = Path("data/raw")
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Primary: PhiUSIIL from UCI
PHIUSIIL_URL = (
    "https://archive.ics.uci.edu/static/public/967/phiusiil+phishing+url+dataset.csv"
)
OUTPUT_FILE = DATA_DIR / "PhiUSIIL_Dataset.csv"

# Fallback: Kaggle dataset (different column names)
KAGGLE_URL = None  # Must be downloaded manually


def download_phiusiil() -> None:
    """Download the PhiUSIIL dataset from UCI."""
    if OUTPUT_FILE.exists():
        logger.info("Dataset already exists at %s — skipping download.", OUTPUT_FILE)
        return

    logger.info("Downloading PhiUSIIL dataset from UCI...")
    try:
        response = requests.get(PHIUSIIL_URL, timeout=120, stream=True)
        response.raise_for_status()

        with open(OUTPUT_FILE, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        logger.info("Downloaded to %s", OUTPUT_FILE)

        df = pd.read_csv(OUTPUT_FILE)
        logger.info("Dataset shape: %s", df.shape)
        logger.info("Columns: %s", list(df.columns)[:10])

        if "URL" in df.columns and "label" in df.columns:
            logger.info(
                "Verified: URL and label columns present. "
                "Phishing: %d, Legitimate: %d",
                df["label"].sum(),
                (df["label"] == 0).sum(),
            )
        else:
            logger.warning(
                "Expected columns 'URL' and 'label' not found. "
                "Available columns: %s",
                list(df.columns),
            )
    except requests.RequestException as exc:
        logger.error("Download failed: %s", exc)
        logger.error(
            "Please download manually from: "
            "https://archive.ics.uci.edu/dataset/967/phiusiil+phishing+url+dataset "
            "and save to %s",
            OUTPUT_FILE,
        )


if __name__ == "__main__":
    download_phiusiil()
