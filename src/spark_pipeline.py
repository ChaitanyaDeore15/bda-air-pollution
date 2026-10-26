"""
Production PySpark Big Data Processing Pipeline.
Performs distributed ingestion of 47M raw records, cleaning, joins with station metadata,
Parquet storage, and pre-computed analytical views.
"""

import sys
import os
import time
import json
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import src.config as config
from src.clean_data import clean_measurements_df, compute_quality_summary
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col,
    avg,
    min,
    max,
    count,
    round,
    first,
    expr,
)

def create_spark_session(app_name: str = "IndiaAirQualityPipeline") -> SparkSession:
    """Creates a tuned PySpark SparkSession for local multicore execution."""
    spark = (
        SparkSession.builder
        .appName(app_name)
        .master("local[*]")
        .config("spark.sql.shuffle.partitions", "8")
        .config("spark.driver.memory", "4g")
        .config("spark.driver.maxResultSize", "2g")
        .config("spark.sql.parquet.compression.codec", "snappy")
        .config("spark.ui.enabled", "false")
        .getOrCreate()
    )
    return spark


def run_pipeline():
    print("=" * 70)
    print("STARTING PYSPARK BIG DATA PIPELINE (HISTORICAL YEAR 2024)")
    print("=" * 70)
    
    start_total_time = time.time()
    spark = create_spark_session()
    print(f"SparkSession created successfully. Spark Version: {spark.version}")

    # 1. Distributed Ingestion of Raw Data (Using concrete resolved paths to bypass Windows Hadoop globbing)
    raw_files = [str(f.resolve()) for f in sorted((config.DATA_RAW_DIR / "year=2024").rglob("*.parquet"))]
    stations_path = config.DATA_METADATA_DIR / "stations.parquet"

    print(f"\n[1/5] Ingesting {len(raw_files)} raw measurement files from year 2024...")
    t0 = time.time()
    df_raw = spark.read.parquet(*raw_files)
    raw_count = df_raw.count()
    ingest_time = time.time() - t0
    print(f"  -> Ingested {raw_count:,} raw records across 12 monthly partitions in {ingest_time:.2f}s")

    # Ingest stations metadata
    print(f"  -> Ingesting station metadata from: {stations_path}")
    df_stations = spark.read.parquet(str(stations_path))
    stations_meta = df_stations.select(
        col("station_id"),
        col("latitude"),
        col("longitude")
    ).dropDuplicates(["station_id"])

    # 2. Cleaning and Validation
    print("\n[2/5] Cleaning and applying physical plausibility rules...")
    t1 = time.time()
    df_cleaned = clean_measurements_df(df_raw)
    
    # Join with station coordinates
    df_joined = df_cleaned.join(stations_meta, on="station_id", how="left")

    # 3. Scalable Storage (Partitioned Parquet)
    processed_parquet_path = config.DATA_PROCESSED_DIR / "clean_measurements_2024.parquet"
    print(f"\n[3/5] Saving cleaned dataset to Parquet: {processed_parquet_path}")
    t2 = time.time()
    (
        df_joined.write
        .partitionBy("obs_month")
        .mode("overwrite")
        .parquet(str(processed_parquet_path))
    )
    save_time = time.time() - t2
    print(f"  -> Parquet write completed in {save_time:.2f}s")

    # Ingest clean Parquet with columnar projection
    df_clean_parquet = spark.read.parquet(str(processed_parquet_path))
    clean_count = df_clean_parquet.count()
    cleaning_time = time.time() - t1
    print(f"  -> Cleaned record count: {clean_count:,} (Removed {raw_count - clean_count:,} invalid/duplicate records) in {cleaning_time:.2f}s")
    print(f"  -> Data Retention Rate: {(clean_count / raw_count * 100):.2f}%")

    # Save Data Quality Report
    quality_metrics = compute_quality_summary(df_raw, df_clean_parquet)
    quality_metrics["ingest_time_seconds"] = float(f"{ingest_time:.2f}")
    quality_metrics["cleaning_time_seconds"] = float(f"{cleaning_time:.2f}")
    quality_metrics["save_time_seconds"] = float(f"{save_time:.2f}")
    quality_path = config.OUTPUTS_METRICS_DIR / "data_quality_summary.json"
    with open(quality_path, "w", encoding="utf-8") as f:
        json.dump(quality_metrics, f, indent=2)
    print(f"  -> Saved data quality metrics to: {quality_path}")

    # 4. Generate Pre-aggregated Analytical Views
    print("\n[4/5] Executing Spark SQL Aggregations and Analytical Summaries...")
    df_clean_parquet.createOrReplaceTempView("clean_measurements")

    # A. Monthly City-Level Summary for Key Pollutants (PM2.5, PM10, NO2, SO2, CO, O3)
    print("  -> Computing monthly city averages...")
    city_monthly_query = """
    SELECT 
        city_name,
        state_name,
        obs_month,
        season,
        ROUND(AVG(CASE WHEN parameter_name = 'PM2.5' THEN value END), 2) as avg_pm25,
        ROUND(AVG(CASE WHEN parameter_name = 'PM10' THEN value END), 2) as avg_pm10,
        ROUND(AVG(CASE WHEN parameter_name = 'NO2' THEN value END), 2) as avg_no2,
        ROUND(AVG(CASE WHEN parameter_name = 'SO2' THEN value END), 2) as avg_so2,
        ROUND(AVG(CASE WHEN parameter_name = 'CO' THEN value END), 2) as avg_co,
        ROUND(AVG(CASE WHEN parameter_name = 'O3' THEN value END), 2) as avg_o3,
        COUNT(CASE WHEN parameter_name = 'PM2.5' THEN 1 END) as pm25_valid_hours,
        COUNT(*) as total_observations
    FROM clean_measurements
    WHERE city_name IS NOT NULL AND city_name != ''
    GROUP BY city_name, state_name, obs_month, season
    """
    df_city_monthly = spark.sql(city_monthly_query)
    city_monthly_pd = df_city_monthly.toPandas()
    city_monthly_csv = config.OUTPUTS_TABLES_DIR / "monthly_city_summary.csv"
    city_monthly_pd.to_csv(city_monthly_csv, index=False)
    print(f"     Saved {len(city_monthly_pd)} monthly city rows to: {city_monthly_csv}")

    # B. Diurnal / Hourly Patterns by City and Season
    print("  -> Computing hourly diurnal pollution patterns...")
    hourly_query = """
    SELECT 
        city_name,
        season,
        obs_hour,
        ROUND(AVG(CASE WHEN parameter_name = 'PM2.5' THEN value END), 2) as avg_pm25,
        ROUND(AVG(CASE WHEN parameter_name = 'PM10' THEN value END), 2) as avg_pm10,
        ROUND(AVG(CASE WHEN parameter_name = 'NO2' THEN value END), 2) as avg_no2,
        COUNT(*) as hour_obs_count
    FROM clean_measurements
    WHERE parameter_name IN ('PM2.5', 'PM10', 'NO2')
    GROUP BY city_name, season, obs_hour
    """
    df_hourly = spark.sql(hourly_query)
    df_hourly_pd = df_hourly.toPandas()
    hourly_csv = config.OUTPUTS_TABLES_DIR / "hourly_pattern_summary.csv"
    df_hourly_pd.to_csv(hourly_csv, index=False)
    print(f"     Saved hourly patterns to: {hourly_csv}")

    # C. Station-Level Ranking & Observation Completeness
    print("  -> Computing station-level rankings and completeness...")
    station_ranking_query = """
    SELECT 
        station_id,
        FIRST(station_name) as station_name,
        FIRST(city_name) as city_name,
        FIRST(state_name) as state_name,
        FIRST(latitude) as latitude,
        FIRST(longitude) as longitude,
        COUNT(CASE WHEN parameter_name = 'PM2.5' THEN 1 END) as pm25_readings,
        ROUND(AVG(CASE WHEN parameter_name = 'PM2.5' THEN value END), 2) as avg_pm25,
        ROUND(STDDEV(CASE WHEN parameter_name = 'PM2.5' THEN value END), 2) as std_pm25,
        ROUND(MAX(CASE WHEN parameter_name = 'PM2.5' THEN value END), 2) as max_pm25,
        ROUND(COUNT(CASE WHEN parameter_name = 'PM2.5' AND value > 60.0 THEN 1 END) * 100.0 / 
              NULLIF(COUNT(CASE WHEN parameter_name = 'PM2.5' THEN 1 END), 0), 2) as pct_exceeding_naaqs
    FROM clean_measurements
    GROUP BY station_id
    HAVING pm25_readings >= 1000
    ORDER BY avg_pm25 DESC
    """
    df_station_rank = spark.sql(station_ranking_query)
    df_station_pd = df_station_rank.toPandas()
    station_csv = config.OUTPUTS_TABLES_DIR / "station_ranking_summary.csv"
    df_station_pd.to_csv(station_csv, index=False)
    print(f"     Saved {len(df_station_pd)} qualified stations to: {station_csv}")

    # D. State Seasonal Comparisons
    print("  -> Computing state seasonal averages...")
    state_seasonal_query = """
    SELECT 
        state_name,
        season,
        ROUND(AVG(CASE WHEN parameter_name = 'PM2.5' THEN value END), 2) as avg_pm25,
        ROUND(AVG(CASE WHEN parameter_name = 'PM10' THEN value END), 2) as avg_pm10,
        ROUND(AVG(CASE WHEN parameter_name = 'NO2' THEN value END), 2) as avg_no2,
        COUNT(*) as total_obs
    FROM clean_measurements
    WHERE state_name IS NOT NULL AND state_name != ''
    GROUP BY state_name, season
    ORDER BY state_name, season
    """
    df_state_seasonal = spark.sql(state_seasonal_query)
    state_seasonal_pd = df_state_seasonal.toPandas()
    state_csv = config.OUTPUTS_TABLES_DIR / "seasonal_summary.csv"
    state_seasonal_pd.to_csv(state_csv, index=False)
    print(f"     Saved state seasonal summary to: {state_csv}")

    # 5. Overall Pipeline Execution Metrics
    total_elapsed = time.time() - start_total_time
    metrics = {
        "dataset_year": 2024,
        "input_records": raw_count,
        "valid_records": clean_count,
        "filtered_records": raw_count - clean_count,
        "retention_percentage": float(f"{(clean_count / raw_count * 100):.2f}"),
        "total_elapsed_seconds": float(f"{total_elapsed:.2f}"),
        "spark_master": spark.sparkContext.master,
        "spark_version": spark.version,
    }
    metrics_path = config.OUTPUTS_METRICS_DIR / "spark_pipeline_metrics.json"
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    print(f"\n[5/5] Pipeline successfully completed in {total_elapsed:.1f}s!")
    print(f"Execution metrics saved to: {metrics_path}")

    spark.stop()
    return metrics

if __name__ == "__main__":
    run_pipeline()
