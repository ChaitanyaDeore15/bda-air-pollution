"""
Environmental Data Analytics Module.
Calculates temporal trends (hourly, monthly, seasonal), multi-pollutant correlations,
and pollution episode statistics.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import src.config as config

def analyze_correlations(city_monthly_csv: Path = config.OUTPUTS_TABLES_DIR / "monthly_city_summary.csv"):
    """Computes correlation matrix between major air pollutants using pairwise observations."""
    print("Computing pollutant correlations...")
    df = pd.read_csv(city_monthly_csv)
    
    pollutants = ["avg_pm25", "avg_pm10", "avg_no2", "avg_so2", "avg_co", "avg_o3"]
    cols_present = [p for p in pollutants if p in df.columns]
    
    # Compute pairwise Pearson correlation
    corr_matrix = df[cols_present].corr(method="pearson", min_periods=10).round(3)
    
    name_map = {
        "avg_pm25": "PM2.5",
        "avg_pm10": "PM10",
        "avg_no2": "NO2",
        "avg_so2": "SO2",
        "avg_co": "CO",
        "avg_o3": "O3",
    }
    corr_matrix.columns = [name_map.get(c, c) for c in corr_matrix.columns]
    corr_matrix.index = [name_map.get(c, c) for c in corr_matrix.index]
    
    # Ensure diagonal is 1.0
    for c in corr_matrix.columns:
        corr_matrix.loc[c, c] = 1.0
    
    corr_csv = config.OUTPUTS_TABLES_DIR / "pollutant_correlation_matrix.csv"
    corr_matrix.to_csv(corr_csv)
    print(f"Saved correlation matrix to: {corr_csv}")
    print(corr_matrix)

    # Generate Heatmap
    plt.figure(figsize=(8, 6), dpi=120)
    sns.set_theme(style="white")
    mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
    cmap = sns.diverging_palette(230, 20, as_cmap=True)

    sns.heatmap(
        corr_matrix,
        mask=mask,
        cmap=cmap,
        vmax=1.0,
        vmin=-1.0,
        center=0,
        square=True,
        linewidths=0.8,
        annot=True,
        fmt=".2f",
        cbar_kws={"shrink": 0.8}
    )
    plt.title("Inter-Pollutant Pearson Correlation Matrix (India 2024)", fontsize=13, weight="bold")
    plt.tight_layout()
    chart_path = config.OUTPUTS_CHARTS_DIR / "05_pollutant_correlation_heatmap.png"
    plt.savefig(chart_path)
    plt.close()
    print(f"Saved correlation heatmap to: {chart_path}")
    return corr_matrix


def analyze_diurnal_patterns(hourly_csv: Path = config.OUTPUTS_TABLES_DIR / "hourly_pattern_summary.csv"):
    """Analyzes 24-hour diurnal pollution variations across seasons."""
    print("Analyzing diurnal hourly patterns...")
    df = pd.read_csv(hourly_csv)
    
    # Aggregate across cities by season and hour
    diurnal = df.groupby(["season", "obs_hour"])[["avg_pm25", "avg_no2"]].mean().reset_index()

    fig, ax1 = plt.subplots(figsize=(11, 5), dpi=120)
    sns.set_theme(style="whitegrid")

    palette = {"Winter": "#d73027", "Summer / Pre-Monsoon": "#fdae6b", "Monsoon": "#4575b4", "Post-Monsoon": "#762a83"}

    for season_name, grp in diurnal.groupby("season"):
        ax1.plot(
            grp["obs_hour"],
            grp["avg_pm25"],
            marker="o",
            linewidth=2.2,
            label=f"PM2.5 ({season_name})",
            color=palette.get(season_name, "#333333")
        )

    ax1.set_xlabel("Hour of Day (IST)", fontsize=11)
    ax1.set_ylabel("Mean PM2.5 Concentration (µg/m³)", fontsize=11)
    ax1.set_title("24-Hour Diurnal PM2.5 Concentration Profiles by Season (India 2024)", fontsize=13, weight="bold")
    ax1.set_xticks(range(0, 24))
    ax1.grid(True, linestyle="--", alpha=0.6)
    ax1.legend(title="Season", loc="upper right")
    plt.tight_layout()

    chart_path = config.OUTPUTS_CHARTS_DIR / "04_diurnal_hourly_pattern.png"
    plt.savefig(chart_path)
    plt.close()
    print(f"Saved diurnal pattern chart to: {chart_path}")


def analyze_seasonal_shifts(seasonal_csv: Path = config.OUTPUTS_TABLES_DIR / "seasonal_summary.csv"):
    """Analyzes the dramatic seasonal shifts between Monsoon wash-out and Winter stagnation."""
    print("Analyzing seasonal shifts across states...")
    df = pd.read_csv(seasonal_csv)

    # Focus on top 10 states with highest observation coverage
    top_states = (
        df.groupby("state_name")["total_obs"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
        .index.tolist()
    )
    df_top = df[df["state_name"].isin(top_states)]

    plt.figure(figsize=(12, 6), dpi=120)
    sns.set_theme(style="whitegrid")

    palette = ["#4575b4", "#fee08b", "#f46d43", "#a50026"]
    sns.barplot(
        data=df_top,
        x="state_name",
        y="avg_pm25",
        hue="season",
        palette=palette
    )
    plt.axhline(60.0, color="navy", linestyle="--", linewidth=1.5, label="NAAQS 24-Hr Standard (60 µg/m³)")
    plt.title("Seasonal PM2.5 Disparity Across Major States in India (2024)", fontsize=13, weight="bold")
    plt.xlabel("State", fontsize=11)
    plt.ylabel("Mean PM2.5 (µg/m³)", fontsize=11)
    plt.xticks(rotation=25, ha="right")
    plt.legend(title="Season", loc="upper right")
    plt.tight_layout()

    chart_path = config.OUTPUTS_CHARTS_DIR / "04_seasonal_pollution_shift.png"
    plt.savefig(chart_path)
    plt.close()
    print(f"Saved seasonal shift chart to: {chart_path}")

if __name__ == "__main__":
    analyze_correlations()
    analyze_diurnal_patterns()
    analyze_seasonal_shifts()
