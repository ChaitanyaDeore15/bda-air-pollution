"""
PM2.5 Forecasting and Predictive Analytics Module.
Implements a strict chronological time-series experiment comparing:
1. Persistence Baseline (Lag 1h, Lag 24h)
2. 24-Hour Rolling Average Baseline
3. Ridge Regression with Temporal & Lag Features
4. Gradient Boosting Regressor
Evaluates MAE, RMSE, and R2 on holdout winter test set (Nov-Dec 2024).
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import Ridge
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import src.config as config

def build_forecasting_dataset(city: str = "Delhi") -> pd.DataFrame:
    """
    Extracts hourly time-series for a selected hotspot city from raw files.
    """
    print(f"Building chronological forecasting dataset for {city}...")
    
    # We can load Delhi measurements across the months
    raw_files = sorted((config.DATA_RAW_DIR / "year=2024").rglob("*.parquet"))
    records = []
    
    for f in raw_files:
        df_month = pd.read_parquet(f, columns=["city_name", "parameter_name", "collected_at", "value"])
        df_city = df_month[(df_month["city_name"] == city) & (df_month["parameter_name"].isin(["PM2.5", "NO2", "CO"]))]
        records.append(df_city)
        
    df_all = pd.concat(records, ignore_index=True)
    df_all["collected_at"] = pd.to_datetime(df_all["collected_at"])
    
    # Pivot to wide format: timestamp as index, pollutants as columns
    df_wide = df_all.pivot_table(
        index="collected_at",
        columns="parameter_name",
        values="value",
        aggfunc="mean"
    ).sort_index()

    # Resample to strict hourly frequency and interpolate short gaps (< 3 hours)
    df_hourly = df_wide.resample("1h").mean().interpolate(method="time", limit=3)
    df_hourly = df_hourly.dropna(subset=["PM2.5"]).copy()

    # Feature Engineering (Lags and Temporal)
    df_hourly["lag_1"] = df_hourly["PM2.5"].shift(1)
    df_hourly["lag_2"] = df_hourly["PM2.5"].shift(2)
    df_hourly["lag_3"] = df_hourly["PM2.5"].shift(3)
    df_hourly["lag_24"] = df_hourly["PM2.5"].shift(24)
    df_hourly["rolling_mean_24"] = df_hourly["PM2.5"].shift(1).rolling(24).mean()

    df_hourly["hour"] = df_hourly.index.hour
    df_hourly["month"] = df_hourly.index.month
    df_hourly["dayofweek"] = df_hourly.index.dayofweek

    # Drop rows with NaN in lags
    df_clean = df_hourly.dropna().copy()
    print(f"Constructed {len(df_clean)} hourly feature records for {city} (2024).")
    return df_clean


def run_forecasting_experiment(df: pd.DataFrame):
    """
    Executes chronological train/validation/test split and evaluates models.
    """
    print("\nRunning forecasting experiment with strict chronological split...")
    
    # Chronological Split:
    # Train: Jan - Sep 2024 (Months 1-9)
    # Val: Oct 2024 (Month 10)
    # Test: Nov - Dec 2024 (Months 11-12 - severe pollution episode season)
    train_mask = df["month"] <= 9
    val_mask = df["month"] == 10
    test_mask = df["month"] >= 11

    feature_cols = ["lag_1", "lag_2", "lag_3", "lag_24", "rolling_mean_24", "hour", "month", "dayofweek"]
    if "NO2" in df.columns:
        feature_cols.append("NO2")
    if "CO" in df.columns:
        feature_cols.append("CO")

    X_train, y_train = df.loc[train_mask, feature_cols], df.loc[train_mask, "PM2.5"]
    X_test, y_test = df.loc[test_mask, feature_cols], df.loc[test_mask, "PM2.5"]

    print(f"Train samples: {len(X_train)} | Test samples: {len(X_test)}")

    # 1. Baseline 1: Persistence (y_pred = lag_1)
    y_pred_persist = X_test["lag_1"]
    mae_persist = mean_absolute_error(y_test, y_pred_persist)
    rmse_persist = np.sqrt(mean_squared_error(y_test, y_pred_persist))
    r2_persist = r2_score(y_test, y_pred_persist)

    # 2. Baseline 2: 24h Rolling Mean
    y_pred_roll = X_test["rolling_mean_24"]
    mae_roll = mean_absolute_error(y_test, y_pred_roll)
    rmse_roll = np.sqrt(mean_squared_error(y_test, y_pred_roll))
    r2_roll = r2_score(y_test, y_pred_roll)

    # 3. Model: Ridge Regression
    ridge = Ridge(alpha=1.0)
    ridge.fit(X_train, y_train)
    y_pred_ridge = ridge.predict(X_test)
    mae_ridge = mean_absolute_error(y_test, y_pred_ridge)
    rmse_ridge = np.sqrt(mean_squared_error(y_test, y_pred_ridge))
    r2_ridge = r2_score(y_test, y_pred_ridge)

    # 4. Model: Gradient Boosting Regressor
    gbr = GradientBoostingRegressor(n_estimators=100, max_depth=4, random_state=42)
    gbr.fit(X_train, y_train)
    y_pred_gbr = gbr.predict(X_test)
    mae_gbr = mean_absolute_error(y_test, y_pred_gbr)
    rmse_gbr = np.sqrt(mean_squared_error(y_test, y_pred_gbr))
    r2_gbr = r2_score(y_test, y_pred_gbr)

    results = {
        "Persistence_Lag1": {"MAE": round(mae_persist, 2), "RMSE": round(rmse_persist, 2), "R2": round(r2_persist, 3)},
        "Rolling_Mean_24h": {"MAE": round(mae_roll, 2), "RMSE": round(rmse_roll, 2), "R2": round(r2_roll, 3)},
        "Ridge_Regression": {"MAE": round(mae_ridge, 2), "RMSE": round(rmse_ridge, 2), "R2": round(r2_ridge, 3)},
        "Gradient_Boosting": {"MAE": round(mae_gbr, 2), "RMSE": round(rmse_gbr, 2), "R2": round(r2_gbr, 3)},
    }

    print("\nModel Evaluation Results on Winter Holdout Set (Nov-Dec 2024):")
    for m, score in results.items():
        print(f"  {m:<20} | MAE: {score['MAE']:<6.2f} µg/m³ | RMSE: {score['RMSE']:<6.2f} µg/m³ | R2: {score['R2']}")

    # Save metrics to JSON
    metrics_path = config.OUTPUTS_METRICS_DIR / "forecasting_metrics.json"
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    # Plot Actual vs Predicted (Zoomed in on a 7-day severe episode in November 2024)
    plot_df = pd.DataFrame({
        "Actual": y_test,
        "Persistence": y_pred_persist,
        "GradientBoosting": y_pred_gbr,
    }, index=y_test.index)

    # Focus on a representative 7-day severe episode: Nov 10 to Nov 17, 2024
    episode_df = plot_df["2024-11-10":"2024-11-17"]

    plt.figure(figsize=(12, 5), dpi=120)
    sns.set_theme(style="whitegrid")
    plt.plot(episode_df.index, episode_df["Actual"], label="Measured PM2.5 (Observation)", color="black", linewidth=2.0)
    plt.plot(episode_df.index, episode_df["GradientBoosting"], label="Gradient Boosting Forecast", color="red", linestyle="--", linewidth=1.8)
    plt.plot(episode_df.index, episode_df["Persistence"], label="Persistence Baseline", color="gray", linestyle=":", alpha=0.7)

    plt.title("PM2.5 1-Hour Ahead Forecast vs Actual Measurements (Delhi Winter Episode Nov 2024)", fontsize=13, weight="bold")
    plt.xlabel("Date & Time (IST)", fontsize=11)
    plt.ylabel("PM2.5 (µg/m³)", fontsize=11)
    plt.legend(loc="upper right")
    plt.tight_layout()

    chart_path = config.OUTPUTS_CHARTS_DIR / "05_pm25_forecasting_evaluation.png"
    plt.savefig(chart_path)
    plt.close()
    print(f"Saved forecasting evaluation chart to: {chart_path}")
    return results

if __name__ == "__main__":
    df_fc = build_forecasting_dataset(city="Delhi")
    run_forecasting_experiment(df_fc)
