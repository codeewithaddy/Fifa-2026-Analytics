"""
refresh_data.py — Data refresh for FIFA 2026 Intelligence Hub
Downloads the latest players.csv from Kaggle and updates the cache timestamp.

Usage (local):
  .\venv\Scripts\python.exe refresh_data.py

Usage (Render cron):
  Set KAGGLE_USERNAME and KAGGLE_KEY as environment variables on the Render dashboard.
  Runs every 6 hours via render.yaml cron job.
"""

import os
import sys
import json
import time
import shutil
import pathlib
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

ROOT      = pathlib.Path(__file__).parent
DATA_DIR  = ROOT / "data"
CSV_NAME  = "players.csv"
CACHE_FILE = DATA_DIR / "api_cache.json"

# Kaggle dataset identifier
KAGGLE_DATASET = "jahanavirshad/fifa-world-cup-2026-player-stats"
KAGGLE_FILE    = "players.csv"


def setup_kaggle_credentials() -> bool:
    """
    Configure Kaggle API from environment variables OR from streamlit secrets.
    Returns True if credentials are available.
    """
    # 1. Try new Kaggle OAuth Token format
    token = os.environ.get("KAGGLE_API_TOKEN")
    
    # 2. Try falling back to Streamlit secrets (for Community Cloud)
    if not token:
        try:
            import streamlit as st
            if "KAGGLE_API_TOKEN" in st.secrets:
                token = st.secrets["KAGGLE_API_TOKEN"]
        except Exception:
            pass
            
    if token:
        os.environ["KAGGLE_API_TOKEN"] = token
        log.info("Kaggle credentials loaded via KAGGLE_API_TOKEN.")
        return True

    # 3. Try legacy KAGGLE_USERNAME / KAGGLE_KEY
    username = os.environ.get("KAGGLE_USERNAME")
    key      = os.environ.get("KAGGLE_KEY")
    if not username or not key:
        try:
            import streamlit as st
            username = st.secrets.get("KAGGLE_USERNAME")
            key      = st.secrets.get("KAGGLE_KEY")
        except Exception:
            pass

    if username and key:
        os.environ["KAGGLE_USERNAME"] = username
        os.environ["KAGGLE_KEY"]      = key
        log.info("Kaggle credentials loaded via USERNAME/KEY.")
        return True

    log.error("No Kaggle credentials found! Please set KAGGLE_API_TOKEN.")
    return False


def download_dataset() -> bool:
    """Download the latest players.csv from Kaggle."""
    try:
        import kaggle  # noqa: F401 — must be imported after env vars are set
        from kaggle.api.kaggle_api_extended import KaggleApiExtended

        api = KaggleApiExtended()
        api.authenticate()

        DATA_DIR.mkdir(parents=True, exist_ok=True)
        tmp_dir = ROOT / "_tmp_kaggle"
        tmp_dir.mkdir(exist_ok=True)

        log.info(f"Downloading dataset: {KAGGLE_DATASET}…")
        api.dataset_download_files(
            KAGGLE_DATASET,
            path=str(tmp_dir),
            unzip=True,
            quiet=False,
        )

        # Find the CSV
        csv_candidates = list(tmp_dir.rglob("*.csv"))
        if not csv_candidates:
            log.error("No CSV found in downloaded dataset.")
            return False

        # Pick the one matching our expected name, else first CSV
        target_csv = next(
            (p for p in csv_candidates if p.name.lower() == KAGGLE_FILE.lower()),
            csv_candidates[0],
        )

        dest = DATA_DIR / CSV_NAME
        shutil.move(str(target_csv), str(dest))
        log.info(f"✅  Dataset saved to {dest} ({dest.stat().st_size / 1024:.1f} KB)")

        # Cleanup
        shutil.rmtree(tmp_dir, ignore_errors=True)
        return True

    except ImportError:
        log.error("kaggle package not installed. Run: pip install kaggle")
        return False
    except Exception as e:
        log.error(f"Download failed: {e}")
        return False


def validate_data() -> bool:
    """Quick sanity check on the downloaded CSV."""
    import pandas as pd

    csv_path = DATA_DIR / CSV_NAME
    if not csv_path.exists():
        log.error(f"CSV not found at {csv_path}")
        return False

    try:
        df = pd.read_csv(csv_path, nrows=5)
        required = {"player", "team", "goals", "shots", "minutes"}
        missing = required - set(df.columns)
        if missing:
            log.warning(f"Expected columns missing from CSV: {missing}")
            return False
        row_count = sum(1 for _ in open(csv_path)) - 1  # approximate
        log.info(f"✅  Validation passed. ~{row_count} rows, {len(df.columns)} columns.")
        return True
    except Exception as e:
        log.error(f"Validation error: {e}")
        return False


def main():
    log.info("=" * 50)
    log.info("FIFA 2026 Intelligence Hub — Data Refresh")
    log.info("=" * 50)

    if not setup_kaggle_credentials():
        sys.exit(1)

    if not download_dataset():
        sys.exit(1)

    if not validate_data():
        log.warning("Validation failed but file downloaded. Check data manually.")

    log.info("Data refresh complete. ✅")


if __name__ == "__main__":
    main()
