"""
Dashboard Visual Components and Helper Functions for Streamlit.
Provides standardized Plotly figures, metric KPI cards, and styling.
"""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

def render_kpi_card(title: str, value: str, subtext: str = "", delta: str = None):
    """Generates HTML snippet for a sleek KPI card."""
    delta_html = f"<span style='color: #2ca02c; font-size: 14px;'>{delta}</span>" if delta else ""
    return f"""
    <div style="background-color: #f8f9fa; border: 1px solid #e9ecef; border-radius: 8px; padding: 15px; margin-bottom: 10px;">
        <h4 style="margin: 0; color: #6c757d; font-size: 13px; text-transform: uppercase;">{title}</h4>
        <h2 style="margin: 5px 0; color: #212529; font-size: 28px; font-weight: bold;">{value}</h2>
        <p style="margin: 0; color: #868e96; font-size: 12px;">{subtext} {delta_html}</p>
    </div>
    """

def plot_top_cities_bar(df_cities: pd.DataFrame, pollutant_col: str = "avg_pm25", top_n: int = 10):
    """Interactive bar chart of top polluted cities."""
    top = df_cities.groupby("city_name")[pollutant_col].mean().reset_index()
    top = top.sort_values(by=pollutant_col, ascending=False).head(top_n)

    fig = px.bar(
        top,
        x=pollutant_col,
        y="city_name",
        orientation="h",
        color=pollutant_col,
        color_continuous_scale="Reds",
        title=f"Top {top_n} Most Polluted Cities by {pollutant_col.upper()} (2024 Average)",
        labels={pollutant_col: "Concentration (µg/m³)", "city_name": "City"},
    )
    fig.add_vline(x=60.0, line_dash="dash", line_color="blue", annotation_text="NAAQS 24h Standard (60 µg/m³)")
    fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=400, margin=dict(l=10, r=10, t=40, b=10))
    return fig

def plot_diurnal_curve(df_hourly: pd.DataFrame, city: str = None):
    """Interactive line chart of 24-hour diurnal patterns by season."""
    if city and "city_name" in df_hourly.columns and city != "All Cities":
        df = df_hourly[df_hourly["city_name"] == city]
    else:
        df = df_hourly

    diurnal = df.groupby(["season", "obs_hour"])[["avg_pm25", "avg_no2"]].mean().reset_index()

    fig = px.line(
        diurnal,
        x="obs_hour",
        y="avg_pm25",
        color="season",
        markers=True,
        title=f"24-Hour Diurnal PM2.5 Variation by Season ({city or 'National Average'})",
        labels={"obs_hour": "Hour of Day (IST)", "avg_pm25": "PM2.5 (µg/m³)", "season": "Season"},
        color_discrete_map={"Winter": "#d73027", "Summer / Pre-Monsoon": "#fdae6b", "Monsoon": "#4575b4", "Post-Monsoon": "#762a83"}
    )
    fig.update_layout(xaxis=dict(tickmode="linear", tick0=0, dtick=2), height=400, margin=dict(l=10, r=10, t=40, b=10))
    return fig

def plot_spatial_hotspots_map(df_hotspots: pd.DataFrame):
    """Interactive Scatter Map for monitoring stations across India."""
    df_geo = df_hotspots.dropna(subset=["latitude", "longitude"]).copy()
    if df_geo.empty:
        return None

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
            "Critical Persistent Hotspot": "#b30000",
            "High Persistent Hotspot": "#e6550d",
            "Moderate / Seasonal Hotspot": "#fdae6b",
            "Compliant / Low Pollution": "#31a354",
        },
        "zoom": 4.2,
        "center": {"lat": 22.5, "lon": 82.0},
        "title": "Spatial Distribution of Monitoring Stations & Persistent Hotspots (2024)",
        "height": 550,
    }
    kwargs[style_key] = "open-street-map"
    fig = map_func(df_geo, **kwargs)
    fig.update_layout(margin=dict(l=0, r=0, t=40, b=0))
    return fig
