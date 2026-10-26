"""
Unit tests for Data Cleaning and Physical Plausibility Rules.
Uses PySpark and local fixtures without requiring network access.
"""

import pytest
from datetime import datetime
from pyspark.sql import SparkSession
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    DoubleType,
    TimestampType,
)
from src.clean_data import clean_measurements_df, compute_quality_summary

@pytest.fixture(scope="session")
def spark():
    """Shared SparkSession fixture for testing."""
    import src.config
    session = (
        SparkSession.builder
        .appName("TestDataCleaning")
        .master("local[2]")
        .config("spark.sql.shuffle.partitions", "2")
        .config("spark.ui.enabled", "false")
        .getOrCreate()
    )
    yield session
    session.stop()

def test_physical_plausibility_filtering(spark):
    """Verify that negative numbers and impossible extreme values are filtered out."""
    schema = StructType([
        StructField("station_id", StringType(), True),
        StructField("station_name", StringType(), True),
        StructField("state_name", StringType(), True),
        StructField("city_name", StringType(), True),
        StructField("parameter_name", StringType(), True),
        StructField("unit", StringType(), True),
        StructField("collected_at", TimestampType(), True),
        StructField("value", DoubleType(), True),
        StructField("source", StringType(), True),
    ])

    sample_rows = [
        ("ST01", "Station 1", "Delhi", "Delhi", "PM2.5", "ug/m3", datetime(2024, 1, 1, 10, 0), 120.0, "cpcb"),   # Valid
        ("ST01", "Station 1", "Delhi", "Delhi", "PM2.5", "ug/m3", datetime(2024, 1, 1, 11, 0), -5.0, "cpcb"),    # Invalid negative
        ("ST01", "Station 1", "Delhi", "Delhi", "PM2.5", "ug/m3", datetime(2024, 1, 1, 12, 0), 2500.0, "cpcb"),  # Invalid extreme spike (>1500)
        ("ST01", "Station 1", "Delhi", "Delhi", "PM10", "ug/m3", datetime(2024, 1, 1, 10, 0), 180.0, "cpcb"),    # Valid
        ("ST01", "Station 1", "Delhi", "Delhi", "CO", "mg/m3", datetime(2024, 1, 1, 10, 0), 1.5, "cpcb"),        # Valid
    ]

    raw_df = spark.createDataFrame(sample_rows, schema=schema)
    cleaned_df = clean_measurements_df(raw_df)

    # Only 3 valid records should remain
    assert cleaned_df.count() == 3
    values = [r.value for r in cleaned_df.collect()]
    assert -5.0 not in values
    assert 2500.0 not in values

def test_temporal_feature_engineering(spark):
    """Verify that season, hour, day_of_week, and obs_month are correctly derived."""
    schema = StructType([
        StructField("station_id", StringType(), True),
        StructField("station_name", StringType(), True),
        StructField("state_name", StringType(), True),
        StructField("city_name", StringType(), True),
        StructField("parameter_name", StringType(), True),
        StructField("unit", StringType(), True),
        StructField("collected_at", TimestampType(), True),
        StructField("value", DoubleType(), True),
        StructField("source", StringType(), True),
    ])

    rows = [
        ("ST01", "Station 1", "Delhi", "Delhi", "PM2.5", "ug/m3", datetime(2024, 1, 15, 8, 30), 140.0, "cpcb"), # Winter
        ("ST01", "Station 1", "Delhi", "Delhi", "PM2.5", "ug/m3", datetime(2024, 4, 10, 14, 0), 80.0, "cpcb"),   # Summer
        ("ST01", "Station 1", "Delhi", "Delhi", "PM2.5", "ug/m3", datetime(2024, 7, 20, 20, 0), 35.0, "cpcb"),   # Monsoon
        ("ST01", "Station 1", "Delhi", "Delhi", "PM2.5", "ug/m3", datetime(2024, 11, 5, 22, 0), 220.0, "cpcb"),  # Post-Monsoon
    ]

    cleaned_df = clean_measurements_df(spark.createDataFrame(rows, schema=schema))
    records = {r.obs_month: (r.season, r.obs_hour) for r in cleaned_df.collect()}

    assert records[1] == ("Winter", 8)
    assert records[4] == ("Summer / Pre-Monsoon", 14)
    assert records[7] == ("Monsoon", 20)
    assert records[11] == ("Post-Monsoon", 22)

def test_deduplication(spark):
    """Verify that duplicate readings on the same station, parameter, and timestamp are dropped."""
    schema = StructType([
        StructField("station_id", StringType(), True),
        StructField("station_name", StringType(), True),
        StructField("state_name", StringType(), True),
        StructField("city_name", StringType(), True),
        StructField("parameter_name", StringType(), True),
        StructField("unit", StringType(), True),
        StructField("collected_at", TimestampType(), True),
        StructField("value", DoubleType(), True),
        StructField("source", StringType(), True),
    ])

    rows = [
        ("ST01", "Station 1", "Delhi", "Delhi", "PM2.5", "ug/m3", datetime(2024, 1, 1, 10, 0), 120.0, "cpcb"),
        ("ST01", "Station 1", "Delhi", "Delhi", "PM2.5", "ug/m3", datetime(2024, 1, 1, 10, 0), 120.0, "cpcb"), # Exact duplicate
    ]

    cleaned = clean_measurements_df(spark.createDataFrame(rows, schema=schema))
    assert cleaned.count() == 1
