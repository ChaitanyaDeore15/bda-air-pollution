"""
Inspects XKDR API endpoints and downloads metadata and a validated real-data sample.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
import pandas as pd
from src.config import (
    DATA_METADATA_DIR,
    DATA_SAMPLE_DIR,
    DATA_RAW_DIR,
)
from src.api_client import XKDRAPIClient

def run_inspection():
    client = XKDRAPIClient()

    print("1. Fetching dataset metadata (/v1/meta)...")
    meta = client.get_meta()
    meta_path = DATA_METADATA_DIR / "dataset_meta.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    print(f"   Saved metadata to {meta_path}")
    print(f"   Tier: {meta.get('your_tier')}")
    print(f"   Max rows per query: {meta.get('max_rows_per_query')}")
    print(f"   Total measurements in DB: {meta.get('measurements')}")
    print(f"   Total stations: {meta.get('stations')}")
    print(f"   Total parameters: {meta.get('parameters')}")

    print("\n2. Fetching available bulk files (/v1/files)...")
    try:
        files = client.get_files()
        files_path = DATA_METADATA_DIR / "available_files.json"
        with open(files_path, "w", encoding="utf-8") as f:
            json.dump(files, f, indent=2)
        print(f"   Saved files list to {files_path}")
        print(f"   Found {len(files)} files/archives.")
        if files:
            print(f"   Sample files: {files[:3]}")
    except Exception as e:
        print(f"   Bulk files endpoint note: {e}")

    print("\n3. Fetching parameters (/v1/parameters)...")
    parameters = client.get_parameters()
    param_path = DATA_METADATA_DIR / "parameters.json"
    with open(param_path, "w", encoding="utf-8") as f:
        json.dump(parameters, f, indent=2)
    print(f"   Saved parameters to {param_path}")
    print(f"   Parameters found: {len(parameters)}")
    param_df = pd.DataFrame(parameters)
    print(param_df.head(10).to_string())

    print("\n4. Fetching stations (/v1/stations)...")
    stations = client.get_stations()
    stations_path = DATA_METADATA_DIR / "stations.json"
    with open(stations_path, "w", encoding="utf-8") as f:
        json.dump(stations, f, indent=2)
    print(f"   Saved stations to {stations_path}")
    print(f"   Stations found: {len(stations)}")
    stations_df = pd.DataFrame(stations)
    print(f"   Available columns: {list(stations_df.columns)}")
    print(stations_df.head(5)[["station", "city", "state", "latitude", "longitude"] if "station" in stations_df.columns else stations_df.columns[:5]].to_string())

    print("\n5. Fetching real measurements sample for Delhi (Jan 2024)...")
    # Fetch a 10,000 row sample of real observations
    measurements = client.get_measurements(
        city="Delhi",
        start="2024-01-01",
        end="2024-01-15",
        fmt="json",
        limit=10000,
    )
    
    measurements_data = measurements.get("data", measurements) if isinstance(measurements, dict) else measurements
    sample_json_path = DATA_SAMPLE_DIR / "sample_delhi_jan2024.json"
    with open(sample_json_path, "w", encoding="utf-8") as f:
        json.dump(measurements, f, indent=2)
    print(f"   Saved sample JSON to {sample_json_path}")

    # Convert to DataFrame and save sample Parquet & CSV
    df = pd.DataFrame(measurements_data)
    print(f"   Retrieved {len(df)} real observation records!")
    print(f"   Sample DataFrame schema:\n{df.dtypes}")
    print("\n   Sample 5 records:")
    print(df.head(5).to_string())

    sample_parquet_path = DATA_SAMPLE_DIR / "sample_delhi_jan2024.parquet"
    df.to_parquet(sample_parquet_path, index=False)
    print(f"   Saved sample Parquet to {sample_parquet_path}")

    sample_csv_path = DATA_SAMPLE_DIR / "sample_delhi_jan2024.csv"
    df.to_csv(sample_csv_path, index=False)
    print(f"   Saved sample CSV to {sample_csv_path}")

if __name__ == "__main__":
    run_inspection()
