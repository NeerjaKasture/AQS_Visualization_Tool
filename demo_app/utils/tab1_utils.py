import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from typing import Optional, Tuple, Dict, Any

import os

# Path to this file's directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_BASE = os.path.join(BASE_DIR, "../cache/vis_data")
DATA_BASE = os.path.abspath(DATA_BASE)  

def _load_visualization_data(k) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, Dict[str, Any]]:
    x_new_gd = np.load(f"{DATA_BASE}/x_new_gd_n{k}.npy")
    x_deployed = np.load(f"{DATA_BASE}/x_deployed.npy")
    pm25_pred = np.load(f"{DATA_BASE}/pm25_pred_n{k}.npy")
    pm25_true = np.load(f"{DATA_BASE}/pm25_true_n{k}.npy")
    var = pm25_pred - pm25_true
    india_mask = np.load(f"{DATA_BASE}/india_mask.npy")
    return x_new_gd, x_deployed, pm25_pred, pm25_true,var, india_mask

def create_plotly_india_map(
    k: int,
    show_overlay: bool = True,
    colorscale: str = "RdBu_r",
    overlay_opacity: float = 1.0,
) -> go.Figure:
    """Create an interactive Plotly map for India with sensors and var heatmap.

    - Deployed (CPCB) sensors: black circles
    - New sensors: red stars
    - Heatmap overlay: var = pm25_pred - pm25_true, masked to India region

    Args:
        k: Number of optimized sensors to load (used to pick cached files).
        show_overlay: Whether to display the var heatmap overlay.
        colorscale: Plotly colorscale for the heatmap (default: RdBu_r).
        overlay_opacity: Opacity for the heatmap layer.

    Returns:
        Plotly Figure ready for Streamlit via st.plotly_chart.
    """
    # Load cached visualization data (including india_mask)
    x_new_gd, x_deployed, pm25_pred, pm25_true, var, india_mask = _load_visualization_data(k)

    # Select first time slice if applicable
    def first2d(arr: np.ndarray) -> np.ndarray:
        if arr.ndim == 3:
            return arr[0]
        return arr

    var2d = first2d(var)
    india_mask = first2d(india_mask)

    # --- Apply the India mask ---
    if india_mask.shape == var2d.shape:
        masked_var = np.where(india_mask, var2d, np.nan)
    else:
        # Handle flattened mask case
        masked_var = np.full_like(var2d, np.nan)
        masked_var.flat[: len(india_mask)] = np.where(india_mask, var2d.flat[: len(india_mask)], np.nan)
    # ----------------------------

    # Build lat/lon grid matching var2d resolution
    lat_min, lat_max = 8.0, 37.0
    lon_min, lon_max = 68.0, 97.0
    lats = np.linspace(lat_min, lat_max, var2d.shape[0])
    lons = np.linspace(lon_min, lon_max, var2d.shape[1])

    fig = go.Figure()

    # --- Heatmap layer (residual field) ---
    if show_overlay and masked_var.size > 0:
        zmid = 0.0 if any(s in colorscale for s in ["RdBu", "BrBG", "PiYG"]) else None
        fig.add_trace(
            go.Heatmap(
                z=masked_var,
                x=lons,
                y=lats,
                colorscale=colorscale,
                opacity=overlay_opacity,
                showscale=True,
                colorbar=dict(title="Variance"),
                zmid=zmid,
                hovertemplate="Lat: %{y:.2f}<br>Lon: %{x:.2f}<br>var: %{z:.3f}<extra></extra>",
            )
        )

    # --- Optimized sensors (red stars) ---
    if isinstance(x_new_gd, np.ndarray) and x_new_gd.size > 0:
        fig.add_trace(
            go.Scatter(
                x=x_new_gd[:, 1],
                y=x_new_gd[:, 0],
                mode="markers",
                name="New Sensors",
                marker=dict(size=9, color="red", symbol="star", line=dict(width=1, color="white")),
                hovertemplate="<b>Optimum new Sensor</b><br>Lat: %{y:.3f}<br>Lon: %{x:.3f}<extra></extra>",
            )
        )

    # --- Deployed (CPCB) sensors (black dots) ---
    if isinstance(x_deployed, np.ndarray) and x_deployed.size > 0:
        fig.add_trace(
            go.Scatter(
                x=x_deployed[:, 1],
                y=x_deployed[:, 0],
                mode="markers",
                name="CPCB Sensors",
                marker=dict(size=6, color="black", symbol="circle", line=dict(width=1, color="white")),
                hovertemplate="<b>CPCB Sensor</b><br>Lat: %{y:.3f}<br>Lon: %{x:.3f}<extra></extra>",
            )
        )

    # --- Layout ---
    fig.update_layout(
        title=f"India Sensor Map (k={k})",
        xaxis_title="Longitude",
        yaxis_title="Latitude",
        xaxis=dict(range=[lon_min, lon_max], constrain="domain"),
        yaxis=dict(range=[lat_min, lat_max], scaleanchor="x", scaleratio=1),
        height=650,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=0, r=0, t=40, b=0),

        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(color="black"),

    )

    return fig

    