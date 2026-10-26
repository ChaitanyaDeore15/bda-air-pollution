"""
Unit tests for Hotspot Methodology, Correlation Analytics, and Forecasting.
"""

import pytest
import pandas as pd
import numpy as np
from src.hotspot_analysis import compute_hotspots
import src.config as config


def test_hotspot_ranking_structure():
    """Verify that hotspot rankings contain all necessary score components and classifications."""
    csv_path = config.OUTPUTS_TABLES_DIR / "hotspots_ranking.csv"
    assert csv_path.exists(), "hotspots_ranking.csv must exist before running test"

    df = pd.read_csv(csv_path)
    assert not df.empty
    assert "hotspot_score" in df.columns
    assert "classification" in df.columns
    assert "pct_exceeding_naaqs" in df.columns

    # Verify score bounds (0 to 100)
    assert df["hotspot_score"].min() >= 0.0
    assert df["hotspot_score"].max() <= 100.0

    # Verify classifications belong to documented taxonomy
    valid_classes = {
        "Critical Persistent Hotspot",
        "High Persistent Hotspot",
        "Moderate / Seasonal Hotspot",
        "Compliant / Low Pollution",
    }
    assert set(df["classification"].unique()).issubset(valid_classes)


def test_correlation_matrix_properties():
    """Verify that pollutant correlation matrix is mathematically valid."""
    csv_path = config.OUTPUTS_TABLES_DIR / "pollutant_correlation_matrix.csv"
    assert csv_path.exists(), "pollutant_correlation_matrix.csv must exist"

    df_corr = pd.read_csv(csv_path, index_col=0)
    
    # Diagonal must be exactly 1.0
    for col in df_corr.columns:
        assert np.isclose(df_corr.loc[col, col], 1.0)

    # Must be symmetric: corr(A, B) == corr(B, A) (allowing for NaN if sensor absent)
    for col1 in df_corr.columns:
        for col2 in df_corr.columns:
            assert np.isclose(df_corr.loc[col1, col2], df_corr.loc[col2, col1], equal_nan=True)


def test_forecasting_evaluation_metrics():
    """Verify that forecasting metrics exist and models beat naive moving average."""
    metrics_path = config.OUTPUTS_METRICS_DIR / "forecasting_metrics.json"
    assert metrics_path.exists()

    import json
    with open(metrics_path) as f:
        metrics = json.load(f)

    assert "Persistence_Lag1" in metrics
    assert "Ridge_Regression" in metrics
    assert "Gradient_Boosting" in metrics

    # Ridge should improve on 24h rolling mean
    assert metrics["Ridge_Regression"]["MAE"] < metrics["Rolling_Mean_24h"]["MAE"]
