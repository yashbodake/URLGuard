"""Download the PhiUSIIL Phishing URL Dataset using ucimlrepo."""

import logging
from pathlib import Path

import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATA_DIR = Path("data/raw")
DATA_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = DATA_DIR / "PhiUSIIL_Dataset.csv"


def download_phiusiil() -> None:
    """Download the PhiUSIIL dataset from UCI via ucimlrepo."""
    if OUTPUT_FILE.exists():
        logger.info("Dataset already exists at %s — skipping download.", OUTPUT_FILE)
        return

    logger.info("Fetching PhiUSIIL dataset via ucimlrepo...")
    try:
        from ucimlrepo import fetch_ucirepo

        phiusiil = fetch_ucirepo(id=967)
        X = phiusiil.data.features
        y = phiusiil.data.targets

        if "URL" not in X.columns:
            logger.error("No 'URL' column found in dataset features.")
            logger.error("Available columns: %s", list(X.columns))
            return

        df = pd.DataFrame({"URL": X["URL"]})

        # PhiUSIIL labels: 1 = legitimate, 0 = phishing
        # Flip so: 1 = phishing, 0 = legitimate (matching our convention)
        df["label"] = 1 - y["label"].values

        df.to_csv(OUTPUT_FILE, index=False)
        logger.info("Saved to %s", OUTPUT_FILE)
        logger.info("Shape: %s", df.shape)
        logger.info(
            "Label distribution — Phishing: %d, Legitimate: %d",
            (df["label"] == 1).sum(),
            (df["label"] == 0).sum(),
        )

    except ImportError:
        logger.error(
            "ucimlrepo not installed. Run: pip install ucimlrepo"
        )
    except Exception as exc:
        logger.error("Download failed: %s", exc)


if __name__ == "__main__":
    download_phiusiil()
