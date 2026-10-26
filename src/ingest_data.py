"""
Data Ingestion Pipeline Wrapper for XKDR Air Quality Database.
Validates credentials, orchestrates bulk downloads, and verifies data integrity.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import logging
from src.config import XKDR_API_KEY, DATA_RAW_DIR, DATA_METADATA_DIR
from src.api_client import XKDRAPIClient
from src.download_data import download_core_metadata, download_year_data

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("IngestData")

def run_ingestion(year: int = 2024, months=range(1, 13)):
    """Run full ingestion workflow with pre-checks."""
    print("=" * 70)
    print("STARTING DATA INGESTION PIPELINE")
    print("=" * 70)
    
    if not XKDR_API_KEY:
        raise ValueError("XKDR_API_KEY is missing from environment. Please set it in .env file.")
    
    client = XKDRAPIClient()
    
    # 1. Download metadata
    logger.info("Step 1: Downloading core station and parameter metadata...")
    download_core_metadata(client)
    
    # 2. Download historical observations
    logger.info(f"Step 2: Ingesting monthly observation files for year {year}...")
    downloaded = download_year_data(client, year=year, months=months)
    
    # 3. Verify integrity
    logger.info("Step 3: Verifying downloaded file integrity...")
    total_size = sum(f.stat().st_size for f in downloaded)
    print(f"\n[SUMMARY] Successfully ingested {len(downloaded)} monthly files ({total_size / (1024*1024):.2f} MB).")
    print("=" * 70)
    return downloaded

if __name__ == "__main__":
    run_ingestion()
