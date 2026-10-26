"""
End-to-End Pipeline Execution Script.
Orchestrates ingestion, Spark data cleaning, analytical queries, hotspot detection, and forecasting.
"""

import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.ingest_data import run_ingestion
from src.spark_pipeline import run_spark_pipeline
from src.hotspot_analysis import run_hotspot_analysis
from src.analytics import run_analytics_pipeline
from src.forecasting import run_forecasting_pipeline
from src.export_results import summarize_all_outputs

def main():
    print("=" * 80)
    print("RUNNING END-TO-END BIG DATA ANALYTICS PIPELINE")
    print("=" * 80)
    start_total = time.time()
    
    # 1. Ingestion
    print("\n>>> STAGE 1: DATA INGESTION <<<")
    run_ingestion()
    
    # 2. PySpark Processing
    print("\n>>> STAGE 2: PYSPARK DISTRIBUTED DATA PROCESSING <<<")
    run_spark_pipeline()
    
    # 3. Hotspot Analysis
    print("\n>>> STAGE 3: MULTI-CRITERIA HOTSPOT ANALYSIS <<<")
    run_hotspot_analysis()
    
    # 4. Exploratory Analytics
    print("\n>>> STAGE 4: DIURNAL & SEASONAL ANALYTICS <<<")
    run_analytics_pipeline()
    
    # 5. PM2.5 Forecasting
    print("\n>>> STAGE 5: TIME-SERIES FORECASTING EXPERIMENT <<<")
    run_forecasting_pipeline()
    
    # 6. Export Results Manifest
    print("\n>>> STAGE 6: EXPORT & MANIFEST GENERATION <<<")
    summarize_all_outputs()
    
    elapsed = time.time() - start_total
    print("\n" + "=" * 80)
    print(f"PIPELINE COMPLETED SUCCESSFULLY IN {elapsed:.2f} SECONDS ({elapsed/60:.2f} MINUTES)!")
    print("=" * 80)

if __name__ == "__main__":
    main()
