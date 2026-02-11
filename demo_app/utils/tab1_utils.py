import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from typing import Optional, Tuple, Dict, Any
import json
from os.path import join
import os
import geopandas as gpd


# Path to this file's directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_BASE = os.path.join(BASE_DIR, "../cache/vis_data")
DATA_BASE = os.path.abspath(DATA_BASE)  

def _load_visualization_data(k, method="GDMI") -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, Dict[str, Any]]:
    if method == "MaxVar":
        x_new = np.load(f"{DATA_BASE}/x_new_var_n{k}.npy")
        pm25_pred = np.load(f"{DATA_BASE}/pm25_pred_var_n{k}.npy")
    else:
        x_new = np.load(f"{DATA_BASE}/x_new_gd_n{k}.npy")
        pm25_pred = np.load(f"{DATA_BASE}/pm25_pred_n{k}.npy")
    x_deployed = np.load(f"{DATA_BASE}/x_deployed.npy")
    pm25_true = np.load(f"{DATA_BASE}/pm25_true_n{k}.npy")
    var = pm25_pred - pm25_true
    india_mask = np.load(f"{DATA_BASE}/india_mask.npy")
    return x_new, x_deployed, pm25_pred, pm25_true, var, india_mask


def create_plotly_india_map(
    k: int,
    method: str = "GDMI",
    show_overlay: bool = True,
    colorscale: str = "RdYlBu_r",
    overlay_opacity: float = 0.7,
) -> go.Figure:

    # Load predicted/true + sensors + mask
    x_new_gd, x_deployed, pm25_pred, pm25_true, _, india_mask = _load_visualization_data(k, method=method)

    # # Load India shapefile for border
    # gdf = gpd.read_file(os.path.join(BASE_DIR, "../cache/shapefiles/India_Country_Boundary.shp"))
    # gdf = gdf.to_crs("EPSG:4326")

    # helper to drop time dimension
    def first2d(arr):
        return arr[0] if arr.ndim == 3 else arr

    pm_pred = first2d(pm25_pred)
    pm_true = first2d(pm25_true)
    mask2d = first2d(india_mask)

    # === Compute overlay field ===
    var = pm_pred - pm_true   # <-- USE THIS NOW (prediction error)

    # mask it to India
    if mask2d.shape == var.shape:
        masked_var = np.where(mask2d, var, np.nan)
    else:
        masked_var = np.full_like(var, np.nan)
        masked_var.flat[:mask2d.size] = np.where(mask2d, var.flat[:mask2d.size], np.nan)

    # === Load lat/lon scaling ===
    scale_path = os.path.join(BASE_DIR, "scale_dict.json")
    with open(scale_path, "r") as f:
        scales = json.load(f)

    lat_min, lat_max = scales['lat']['min'], scales['lat']['max']
    lon_min, lon_max = scales['lon']['min'], scales['lon']['max']

    # Construct grid coordinates
    lats = np.linspace(lat_min, lat_max, masked_var.shape[0])
    lons = np.linspace(lon_min, lon_max, masked_var.shape[1])

    # === Create Plotly figure ===
    fig = go.Figure()

   
    # === Heatmap (overlay error field) ===
    if show_overlay:
        vmax = np.nanmax(np.abs(masked_var))  # symmetric range around 0

        fig.add_trace(
            go.Heatmap(
                z=masked_var,
                x=lons,
                y=lats,
                colorscale=colorscale,
                opacity=overlay_opacity,
                showscale=True,
                colorbar=dict(title="Prediction Error"),
                zmin=-vmax,
                zmax=+vmax,
                zmid=0,
                hovertemplate="Lat: %{y:.2f}<br>Lon: %{x:.2f}<br>Error: %{z:.2f}<extra></extra>",
            )
        )

    fig.add_trace(
        go.Contour(
            z=mask2d.astype(float),
            x=lons,
            y=lats,
            contours=dict(
                start=0.5, end=0.5, size=1,   # ONE contour level = boundary
                coloring='none'
            ),
            line=dict(color="black", width=1.5),
            hoverinfo="skip",
            showscale=False
        )
    )



    # === New Sensors ===
    if x_new_gd is not None and x_new_gd.size > 0:
        fig.add_trace(go.Scatter(
            x=x_new_gd[:, 1],
            y=x_new_gd[:, 0],
            mode="markers",
            name="New Sensors",
            marker=dict(size=9, color="red"),
            hovertemplate="New Sensor<br>Lat: %{y:.3f}<br>Lon: %{x:.3f}<extra></extra>"
        ))

    # === Existing CPCB Sensors ===
    if x_deployed is not None and x_deployed.size > 0:
        fig.add_trace(go.Scatter(
            x=x_deployed[:, 1],
            y=x_deployed[:, 0],
            mode="markers",
            name="CPCB Sensors",
            marker=dict(size=6, color="black"),
            hovertemplate="CPCB Sensor<br>Lat: %{y:.3f}<br>Lon: %{x:.3f}<extra></extra>"
        ))

    # === Layout ===
    fig.update_layout(
        title=f"India Sensor Map (k={k}, method={method})",
        xaxis=dict(title="Longitude", range=[lon_min, lon_max], constrain="domain"),
        yaxis=dict(title="Latitude", range=[lat_min, lat_max], scaleanchor="x", scaleratio=1),
        height=650,
        margin=dict(l=0, r=0, t=40, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(color="black"),
    )

    return fig
