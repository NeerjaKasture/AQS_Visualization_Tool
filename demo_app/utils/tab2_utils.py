"""
Tab 2 utilities – Fairness-aware sensor placement maps.

Loads cached artefacts produced by ``fairness-aware.py`` and builds
interactive Plotly figures for the Streamlit demo.
"""

import json
import os
from pathlib import Path
from typing import Dict, Optional, Tuple

import numpy as np
import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FAIRNESS_CACHE_DIR = Path(BASE_DIR).parent / "cache" / "fairness_data"
SCALE_DICT_PATH = os.path.join(BASE_DIR, "scale_dict.json")

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

@st.cache_data
def _load_scale_dict() -> Dict:
    with open(SCALE_DICT_PATH, "r") as f:
        return json.load(f)


def _state_slug(state_name: str) -> str:
    return state_name.replace(" ", "_")


def _state_cache_dir(state_name: str, metric: str = "population") -> Path:
    """Return ``cache/fairness_data/<metric>/<State_Name>/``."""
    return FAIRNESS_CACHE_DIR / metric / _state_slug(state_name)


def has_cached_data(state_name: str, metric: str = "population") -> bool:
    """Return True if cached fairness data exists for the given state+metric."""
    d = _state_cache_dir(state_name, metric)
    return (d / "sensors.npz").exists() and (d / "metrics.json").exists()


def get_cached_states(metric: str = "population") -> list:
    """Return list of state names that have cached data for *metric*."""
    metric_dir = FAIRNESS_CACHE_DIR / metric
    if not metric_dir.exists():
        return []
    states = []
    for p in sorted(metric_dir.iterdir()):
        if p.is_dir() and (p / "sensors.npz").exists():
            states.append(p.name.replace("_", " "))
    return states


# ---------------------------------------------------------------------------
# Data loaders (cached by Streamlit)
# ---------------------------------------------------------------------------

@st.cache_data
def load_fairness_sensors(state_name: str, metric: str = "population") -> Dict[str, np.ndarray]:
    """Load all sensor lon/lat arrays from ``sensors.npz``."""
    path = _state_cache_dir(state_name, metric) / "sensors.npz"
    data = np.load(path)
    return {k: data[k] for k in data.files}


@st.cache_data
def load_fairness_metrics(state_name: str, metric: str = "population") -> Dict:
    """Load metrics.json for a state."""
    path = _state_cache_dir(state_name, metric) / "metrics.json"
    with open(path, "r") as f:
        return json.load(f)


@st.cache_data
def load_state_mask(state_name: str, metric: str = "population") -> np.ndarray:
    """Load the 2-D boolean state mask (lat × lon)."""
    path = _state_cache_dir(state_name, metric) / "state_mask.npz"
    return np.load(path)["mask"]


@st.cache_data
def load_overlay_density(state_name: str, metric: str = "population") -> Optional[np.ndarray]:
    """Load the overlay density grid (lat × lon, NaN outside state).

    Looks for ``population_density.npz`` or ``poverty_density.npz``
    inside ``cache/fairness_data/<metric>/<State>/``.
    """
    d = _state_cache_dir(state_name, metric)
    for fname in ("population_density.npz", "poverty_density.npz"):
        path = d / fname
        if path.exists():
            return np.load(path)["density"]
    return None


# ---------------------------------------------------------------------------
# Coordinate helpers
# ---------------------------------------------------------------------------

def _build_grid_coords(mask_shape: Tuple[int, int]):
    """Return (lats, lons) 1-D arrays matching the mask grid."""
    scales = _load_scale_dict()
    lat_min, lat_max = scales["lat"]["min"], scales["lat"]["max"]
    lon_min, lon_max = scales["lon"]["min"], scales["lon"]["max"]
    lats = np.linspace(lat_min, lat_max, mask_shape[0])
    lons = np.linspace(lon_min, lon_max, mask_shape[1])
    return lats, lons


# ---------------------------------------------------------------------------
# Main plotting function
# ---------------------------------------------------------------------------

def create_plotly_state_map(
    state_name: str,
    metric: str = "population",
    show_sensors: str = "all",
    show_density_overlay: bool = True,
    density_opacity: float = 0.75,
    density_colorscale: str = "YlGnBu",
) -> go.Figure:
    """Build an interactive Plotly map for a single state.

    Parameters
    ----------
    state_name : str
        State name matching the cache folder (e.g. ``"Madhya Pradesh"``).
    metric : str
        Fairness metric subfolder (``"population"`` or ``"poverty"``).
    show_sensors : str
        Which sensor sets to display.  One of:

        * ``"baseline"``  – only existing (old) sensors
        * ``"normal"``    – old + normal GD-MI new sensors
        * ``"pop"``       – old + pop-weighted GD-MI new sensors
        * ``"all"``       – old + both sets of new sensors
    show_density_overlay : bool
        Whether to render the population-density heatmap behind the sensors.
    density_opacity : float
        Opacity of the density heatmap layer.
    density_colorscale : str
        Plotly colour scale name for the density overlay.

    Returns
    -------
    go.Figure
    """
    sensors = load_fairness_sensors(state_name, metric)
    state_mask = load_state_mask(state_name, metric)
    lats, lons = _build_grid_coords(state_mask.shape)

    # Compute bounding box from state mask for zoom
    lat_indices, lon_indices = np.where(state_mask)
    lat_pad, lon_pad = 0.5, 0.5
    lat_lo, lat_hi = lats[lat_indices.min()] - lat_pad, lats[lat_indices.max()] + lat_pad
    lon_lo, lon_hi = lons[lon_indices.min()] - lon_pad, lons[lon_indices.max()] + lon_pad

    fig = go.Figure()

    # --- Overlay heatmap (population density or poverty rate) ---
    overlay_label = {"population": "Population<br>Density", "poverty": "Poverty<br>Rate"}.get(metric, metric)
    if show_density_overlay:
        density = load_overlay_density(state_name, metric)
        if density is not None:
            # Crop to bounding box for performance
            lat_mask_idx = (lats >= lat_lo) & (lats <= lat_hi)
            lon_mask_idx = (lons >= lon_lo) & (lons <= lon_hi)
            density_crop = density[np.ix_(lat_mask_idx, lon_mask_idx)]
            lats_crop = lats[lat_mask_idx]
            lons_crop = lons[lon_mask_idx]

            valid = density_crop[~np.isnan(density_crop)]
            vmax = float(np.nanpercentile(valid, 99)) if valid.size > 0 else 1.0

            fig.add_trace(
                go.Heatmap(
                    z=density_crop,
                    x=lons_crop,
                    y=lats_crop,
                    colorscale=density_colorscale,
                    opacity=density_opacity,
                    showscale=True,
                    colorbar=dict(title=overlay_label, x=1.02),
                    zmin=0,
                    zmax=vmax,
                    hovertemplate=(
                        "Lat: %{y:.2f}<br>Lon: %{x:.2f}<br>"
                        "Value: %{z:,.4f}<extra></extra>"
                    ),
                )
            )

    # --- State boundary contour ---
    fig.add_trace(
        go.Contour(
            z=state_mask.astype(float),
            x=lons,
            y=lats,
            contours=dict(start=0.5, end=0.5, size=1, coloring="none"),
            line=dict(color="black", width=1.5),
            hoverinfo="skip",
            showscale=False,
        )
    )

    # --- Sensor scatter layers ---
    old_lon, old_lat = sensors["old_lon"], sensors["old_lat"]

    # Baseline (old) sensors – always shown
    fig.add_trace(
        go.Scatter(
            x=old_lon, y=old_lat,
            mode="markers",
            name="Existing Sensors",
            marker=dict(size=7, color="blue", symbol="circle",
                        line=dict(width=0.5, color="white")),
            hovertemplate="Existing Sensor<br>Lon: %{x:.3f}<br>Lat: %{y:.3f}<extra></extra>",
        )
    )

    if show_sensors in ("normal", "all"):
        fig.add_trace(
            go.Scatter(
                x=sensors["normal_new_lon"], y=sensors["normal_new_lat"],
                mode="markers",
                name="GD-MI New Sensors",
                marker=dict(size=9, color="red", symbol="diamond",
                            line=dict(width=0.5, color="white")),
                hovertemplate="GD-MI New<br>Lon: %{x:.3f}<br>Lat: %{y:.3f}<extra></extra>",
            )
        )

    if show_sensors in ("pop", "all"):
        fig.add_trace(
            go.Scatter(
                x=sensors["pop_new_lon"], y=sensors["pop_new_lat"],
                mode="markers",
                name="Fairness-Aware New Sensors",
                marker=dict(size=9, color="green", symbol="star",
                            line=dict(width=0.5, color="white")),
                hovertemplate="Fairness-Aware New<br>Lon: %{x:.3f}<br>Lat: %{y:.3f}<extra></extra>",
            )
        )

    # --- Layout ---
    fig.update_layout(
        title=f"{state_name}: Sensor Deployment",
        xaxis=dict(title="Longitude", range=[lon_lo, lon_hi], constrain="domain"),
        yaxis=dict(title="Latitude", range=[lat_lo, lat_hi],
                   scaleanchor="x", scaleratio=1),
        height=600,
        margin=dict(l=0, r=0, t=40, b=80),
        legend=dict(orientation="h", yanchor="top", y=-0.15,
                    xanchor="center", x=0.5),
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(color="black"),
    )

    return fig
