"""
Bulk Data Downloader for XKDR India Air Quality Database.
Downloads core metadata and all 12 months of historical observations for 2024 (47M rows).
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import time
import logging
from src.config import (
    API_BASE_URL,
    DATA_METADATA_DIR,
    DATA_RAW_DIR,
    DATA_SAMPLE_DIR,
)
from src.api_client import XKDRAPIClient

logger = logging.getLogger("DataDownloader")

def download_core_metadata(client: XKDRAPIClient):
    """Downloads stations.parquet and parameters.parquet."""
    print("=" * 60)
    print("DOWNLOADING CORE METADATA")
    print("=" * 60)
    
    stations_dest = DATA_METADATA_DIR / "stations.parquet"
    if not stations_dest.exists() or stations_dest.stat().st_size == 0:
        client.download_bulk_file(f"{API_BASE_URL}/v1/files/v1/stations.parquet", stations_dest)
    print(f"  [OK] Stations: {stations_dest} ({stations_dest.stat().st_size / 1024:.1f} KB)")

    params_dest = DATA_METADATA_DIR / "parameters.parquet"
    if not params_dest.exists() or params_dest.stat().st_size == 0:
        client.download_bulk_file(f"{API_BASE_URL}/v1/files/v1/parameters.parquet", params_dest)
    print(f"  [OK] Parameters: {params_dest} ({params_dest.stat().st_size / 1024:.1f} KB)")

def download_year_data(client: XKDRAPIClient, year: int = 2024, months=range(1, 13)):
    """Downloads all monthly Parquet files for the specified year into Hive partitioned format."""
    print("\n" + "=" * 60)
    print(f"DOWNLOADING HISTORICAL OBSERVATIONS FOR YEAR {year}")
    print("=" * 60)
    
    total_downloaded_bytes = 0
    start_all = time.time()
    downloaded_files = []

    for month in months:
        month_str = f"{month:02d}"
        key = f"v1/measurements/year={year}/month={month_str}/data.parquet"
        url = f"{API_BASE_URL}/v1/files/{key}"
        
        # Target Hive partitioned directory: data/raw/year=YYYY/month=MM/data.parquet
        dest_dir = DATA_RAW_DIR / f"year={year}" / f"month={month_str}"
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_file = dest_dir / "data.parquet"

        if dest_file.exists() and dest_file.stat().st_size > 1000:
            print(f"  [EXISTS] Month {year}-{month_str}: {dest_file.stat().st_size / (1024*1024):.2f} MB (Skipping download)")
            downloaded_files.append(dest_file)
            total_downloaded_bytes += dest_file.stat().st_size
            continue

        print(f"  [DOWNLOADING] Month {year}-{month_str} from {key}...")
        client.download_bulk_file(url, dest_file)
        size_mb = dest_file.stat().st_size / (1024 * 1024)
        print(f"  [OK] Saved {year}-{month_str} ({size_mb:.2f} MB)")
        downloaded_files.append(dest_file)
        total_downloaded_bytes += dest_file.stat().st_size

    total_mb = total_downloaded_bytes / (1024 * 1024)
    elapsed = time.time() - start_all
    print("=" * 60)
    print(f"DOWNLOAD COMPLETE: {len(downloaded_files)} files | {total_mb:.2f} MB in {elapsed:.1f}s")
    print("=" * 60)
    return downloaded_files

if __name__ == "__main__":
    client = XKDRAPIClient()
    download_core_metadata(client)
    download_year_data(client, year=2024, months=range(1, 13))
