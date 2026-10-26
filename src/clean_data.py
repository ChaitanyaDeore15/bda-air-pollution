"""
Data Cleaning, Validation, and Standardization Module.
Implements domain-specific environmental data quality rules and temporal feature engineering.
"""

from typing import Dict, Any, List
from pyspark.sql import DataFrame
from pyspark.sql.functions import (
    col,
    when,
    to_timestamp,
    year,
    month,
    dayofmonth,
    hour,
    dayofweek,
    date_format,
    trim,
    upper,
    lit,
    count,
    isnan,
)

# Physically plausible pollutant measurement bounds
VALID_POLLUTANT_BOUNDS = {
    "PM2.5": (0.0, 1500.0),
    "PM10": (0.0, 2000.0),
    "NO2": (0.0, 1000.0),
    "SO2": (0.0, 1000.0),
    "CO": (0.0, 100.0),
    "O3": (0.0, 1000.0),
    "NH3": (0.0, 1000.0),
}

def clean_measurements_df(df: DataFrame) -> DataFrame:
    """
    Cleans raw air quality measurements:
    - Standardizes column names and trims strings
    - Validates collected_at timestamps
    - Filters out impossible physical values (negative numbers or values exceeding extreme physical ceilings)
    - Deduplicates records based on (station_id, parameter_name, collected_at)
    - Engineers temporal features: year, month, day, hour, day_of_week, season
    """
    # 1. Standardize text columns
    cleaned = (
        df.withColumn("station_id", trim(col("station_id")))
        .withColumn("station_name", trim(col("station_name")))
        .withColumn("state_name", trim(col("state_name")))
        .withColumn("city_name", trim(col("city_name")))
        .withColumn("parameter_name", upper(trim(col("parameter_name"))))
        .withColumn("unit", trim(col("unit")))
        .withColumn("source", trim(col("source")))
    )

    # 2. Timestamp standardization
    cleaned = cleaned.withColumn(
        "collected_at",
        to_timestamp(col("collected_at"))
    )

    # 3. Filter valid measurements using physical bounds
    valid_condition = lit(False)
    for param, (low, high) in VALID_POLLUTANT_BOUNDS.items():
        cond = (col("parameter_name") == param) & (col("value") >= low) & (col("value") <= high)
        valid_condition = valid_condition | cond
    
    # Also allow other meteorological parameters (temperature, humidity, wind) if non-negative or within reason
    valid_condition = valid_condition | (
        (~col("parameter_name").isin(list(VALID_POLLUTANT_BOUNDS.keys()))) & 
        (col("value").isNotNull()) & 
        (~isnan(col("value")))
    )

    cleaned = cleaned.filter(valid_condition & col("collected_at").isNotNull())

    # 4. Remove duplicate readings
    cleaned = cleaned.dropDuplicates(["station_id", "parameter_name", "collected_at"])

    # 5. Feature Engineering: Temporal Dimensions
    cleaned = (
        cleaned
        .withColumn("obs_year", year(col("collected_at")))
        .withColumn("obs_month", month(col("collected_at")))
        .withColumn("obs_day", dayofmonth(col("collected_at")))
        .withColumn("obs_hour", hour(col("collected_at")))
        .withColumn("day_of_week", date_format(col("collected_at"), "EEEE"))
        .withColumn(
            "season",
            when(col("obs_month").isin([12, 1, 2]), "Winter")
            .when(col("obs_month").isin([3, 4, 5]), "Summer / Pre-Monsoon")
            .when(col("obs_month").isin([6, 7, 8, 9]), "Monsoon")
            .when(col("obs_month").isin([10, 11]), "Post-Monsoon")
            .otherwise("Unknown")
        )
    )

    return cleaned


def compute_quality_summary(df_raw: DataFrame, df_clean: DataFrame) -> Dict[str, Any]:
    """
    Computes a before-and-after data quality audit report.
    """
    raw_count = df_raw.count()
    clean_count = df_clean.count()
    filtered_count = raw_count - clean_count
    retention_pct = (clean_count / raw_count * 100) if raw_count > 0 else 0.0

    return {
        "raw_record_count": raw_count,
        "clean_record_count": clean_count,
        "filtered_record_count": filtered_count,
        "retention_percentage": float(f"{retention_pct:.2f}"),
    }
