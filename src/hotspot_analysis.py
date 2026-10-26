"""
Pollution Hotspot Identification and Spatial Analytics Module.
Implements a multi-criteria hotspot identification algorithm based on:
1. Mean Concentration
2. Exceedance Frequency (NAAQS standards)
3. Monthly Persistence across 2024
4. Observation Completeness Filter
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import src.config as config

# National Ambient Air Quality Standards (24-Hour standard in ug/m3)
NAAQS_PM25_LIMIT = 60.0
NAAQS_PM10_LIMIT = 100.0

def compute_hotspots(
    station_ranking_csv: Path = config.OUTPUTS_TABLES_DIR / "station_ranking_summary.csv",
    city_monthly_csv: Path = config.OUTPUTS_TABLES_DIR / "monthly_city_summary.csv",
    min_readings: int = 2000,
) -> pd.DataFrame:
    """
    Computes Hotspot Severity Score and categorizes stations across India.
    """
    if not station_ranking_csv.exists():
        raise FileNotFoundError(f"Station ranking summary not found at {station_ranking_csv}. Please run pipeline first.")

    df = pd.read_csv(station_ranking_csv)
    
    # Filter by minimum observation completeness
    df_qualified = df[df["pm25_readings"] >= min_readings].copy()
    
    # Calculate Severity Index Components:
    # 1. Concentration Ratio: station avg / 60 ug/m3
    df_qualified["concentration_ratio"] = df_qualified["avg_pm25"] / NAAQS_PM25_LIMIT

    # 2. Exceedance Factor: percentage of hours exceeding 60 ug/m3
    # 3. Peak Episode Factor: max_pm25 / 60.0
    df_qualified["peak_factor"] = (df_qualified["max_pm25"] / (NAAQS_PM25_LIMIT * 5.0)).clip(0, 1.5)

    # Composite Hotspot Score (0 to 100 scale)
    # 50% Weight on Mean Concentration, 40% on Exceedance Frequency, 10% on Peak Severity
    raw_score = (
        (df_qualified["concentration_ratio"] / 3.0).clip(0, 1.0) * 50.0 +
        (df_qualified["pct_exceeding_naaqs"] / 100.0) * 40.0 +
        (df_qualified["peak_factor"] / 1.5) * 10.0
    )
    df_qualified["hotspot_score"] = raw_score.round(1)

    # Classify Hotspots
    def classify(score, exceed_pct):
        if score >= 75 and exceed_pct >= 60:
            return "Critical Persistent Hotspot"
        elif score >= 60:
            return "High Persistent Hotspot"
        elif score >= 40:
            return "Moderate / Seasonal Hotspot"
        else:
            return "Compliant / Low Pollution"

    df_qualified["classification"] = [
        classify(s, e) for s, e in zip(df_qualified["hotspot_score"], df_qualified["pct_exceeding_naaqs"])
    ]

    df_sorted = df_qualified.sort_values(by="hotspot_score", ascending=False).reset_index(drop=True)
    
    # Save output ranking table
    out_csv = config.OUTPUTS_TABLES_DIR / "hotspots_ranking.csv"
    df_sorted.to_csv(out_csv, index=False)
    print(f"Hotspot analysis completed. Saved {len(df_sorted)} stations to: {out_csv}")
    return df_sorted


def generate_hotspot_visualizations(df_hotspots: pd.DataFrame):
    """Generates publication charts and interactive maps for hotspot analysis."""
    # 1. Top 15 Hotspot Stations Bar Chart
    top15 = df_hotspots.head(15)

    plt.figure(figsize=(12, 6), dpi=120)
    sns.set_theme(style="whitegrid")
    
    palette = {"Critical Persistent Hotspot": "#b30000", "High Persistent Hotspot": "#e6550d", "Moderate / Seasonal Hotspot": "#fdae6b"}
    
    ax = sns.barplot(
        data=top15,
        y="station_name",
        x="avg_pm25",
        hue="classification",
        dodge=False,
        palette=palette
    )
    plt.axvline(60.0, color="navy", linestyle="--", linewidth=1.8, label="NAAQS 24-Hr Standard (60 µg/m³)")
    plt.title("Top 15 Most Persistent PM2.5 Hotspot Stations Across India (2024)", fontsize=14, weight="bold")
    plt.xlabel("Annual Mean PM2.5 (µg/m³)", fontsize=12)
    plt.ylabel("Monitoring Station", fontsize=12)
    plt.legend(title="Classification", loc="lower right")
    plt.tight_layout()

    chart_path = config.OUTPUTS_CHARTS_DIR / "04_hotspot_severity_ranking.png"
    plt.savefig(chart_path)
    plt.close()
    print(f"Saved hotspot ranking chart to: {chart_path}")

    # 2. Interactive Geo Map using Plotly Express (supports both Plotly 6+ scatter_map and legacy scatter_mapbox)
    df_geo = df_hotspots.dropna(subset=["latitude", "longitude"]).copy()
    if not df_geo.empty:
        map_func = getattr(px, "scatter_map", getattr(px, "scatter_mapbox", None))
        style_key = "map_style" if hasattr(px, "scatter_map") else "mapbox_style"
        kwargs = {
            "lat": "latitude",
            "lon": "longitude",
            "color": "classification",
            "size": "avg_pm25",
            "hover_name": "station_name",
            "hover_data": {
                "city_name": True,
                "state_name": True,
                "avg_pm25": ":.1f",
                "pct_exceeding_naaqs": ":.1f%",
                "hotspot_score": True,
                "latitude": False,
                "longitude": False,
            },
            "color_discrete_map": {
                "Critical Persistent Hotspot": "#d73027",
                "High Persistent Hotspot": "#fc8d59",
                "Moderate / Seasonal Hotspot": "#fee08b",
                "Compliant / Low Pollution": "#91cf60",
            },
            "zoom": 4.2,
            "center": {"lat": 22.5, "lon": 82.0},
            "title": "Geographical Distribution of Air Pollution Hotspots in India (2024)",
        }
        kwargs[style_key] = "open-street-map"
        fig = map_func(df_geo, **kwargs)
        fig.update_layout(margin={"r": 0, "t": 40, "l": 0, "b": 0})
        map_html_path = config.OUTPUTS_CHARTS_DIR / "hotspots_map.html"
        fig.write_html(str(map_html_path))
        print(f"Saved interactive hotspot map to: {map_html_path}")

if __name__ == "__main__":
    df_h = compute_hotspots()
    generate_hotspot_visualizations(df_h)
