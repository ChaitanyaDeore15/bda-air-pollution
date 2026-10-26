"""
Execution script to run the complete data ingestion pipeline from XKDR.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.ingest_data import run_ingestion

if __name__ == "__main__":
    print("Executing scripts/run_ingestion.py...")
    run_ingestion()
