"""Lightweight loaders that sit on top of the pre-computed cache.

Everything here reads cached files only — no torch, no GPU, no live
optimisation.  The UI is instant.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
import streamlit as st

ROOT = Path(__file__).parent
CACHE = ROOT / "cache"
LOC_CSV_DIR = CACHE / "loc_csv"
VIS_DIR = CACHE / "vis_data"
FAIRNESS_DIR = CACHE / "fairness_data"
DATA_DIR = ROOT / "data"


# ---------------------------------------------------------------------------
#  Summary JSON  — national RMSE numbers for GD-MI and MaxVar
# ---------------------------------------------------------------------------

@st.cache_data
def load_summary() -> dict:
    with open(VIS_DIR / "summary.json") as f:
        return json.load(f)


METHOD_META = {
    "gdmi": {
        "label": "Gumbel-softmax (GD-MI)",
        "short": "Gumbel",
        "full": "Gumbel-softmax · gradient-descent on mutual information",
        "prefix": "best_sensors_",
        "color": "#c44536",
    },
    "maxvar": {
        "label": "Greedy (MaxVar)",
        "short": "Greedy",
        "full": "Greedy maximum-variance",
        "prefix": "best_sensors_var_",
        "color": "#3c68cf",
    },
}


def available_ks(method: str) -> List[int]:
    """k values that have both summary entries and a coords CSV."""
    summary = load_summary().get(method, {})
    ks_meta = {int(k) for k in summary.keys()}
    prefix = METHOD_META[method]["prefix"]
    ks_csv = {int(p.stem.replace(prefix, "")) for p in LOC_CSV_DIR.glob(f"{prefix}*.csv")
              if p.stem.replace(prefix, "").isdigit()}
    return sorted(ks_meta & ks_csv)


def load_sensor_coords(method: str, k: int) -> pd.DataFrame:
    prefix = METHOD_META[method]["prefix"]
    path = LOC_CSV_DIR / f"{prefix}{k}.csv"
    if not path.exists():
        return pd.DataFrame(columns=["latitude", "longitude", "state"])
    return pd.read_csv(path)


def method_metrics(method: str, k: int) -> Optional[dict]:
    return load_summary().get(method, {}).get(str(k))


# ---------------------------------------------------------------------------
#  Strategy comparison table
# ---------------------------------------------------------------------------

def comparison_table() -> pd.DataFrame:
    """Wide format: one row per (method, k) with real metrics."""
    summary = load_summary()
    rows = []
    for method, data in summary.items():
        for k_str, stats in data.items():
            k = int(k_str)
            rows.append({
                "strategy": METHOD_META.get(method, {}).get("label", method),
                "method_key": method,
                "k": k,
                "rmse_before": stats.get("rmse_before"),
                "rmse_after": stats.get("rmse_after"),
                "pred_rmse": stats.get("pred_rmse"),
                "improvement_pct": stats.get("improvement_percent"),
                "final_loss": stats.get("best_loss") or stats.get("final_loss"),
                "n_runs": stats.get("n_files_found"),
            })
    df = pd.DataFrame(rows).sort_values(["k", "strategy"]).reset_index(drop=True)
    return df


# ---------------------------------------------------------------------------
#  Fairness cache (per state)
# ---------------------------------------------------------------------------

def available_states(metric: str) -> List[str]:
    d = FAIRNESS_DIR / metric
    if not d.exists():
        return []
    return sorted(
        p.name.replace("_", " ")
        for p in d.iterdir()
        if p.is_dir() and (p / "sensors.npz").exists()
    )


def available_fairness_metrics() -> List[str]:
    if not FAIRNESS_DIR.exists():
        return []
    return sorted(p.name for p in FAIRNESS_DIR.iterdir() if p.is_dir())


def _state_dir(state: str, metric: str) -> Path:
    return FAIRNESS_DIR / metric / state.replace(" ", "_")


@st.cache_data
def load_state_metrics(state: str, metric: str) -> dict:
    with open(_state_dir(state, metric) / "metrics.json") as f:
        return json.load(f)


@st.cache_data
def load_state_sensors(state: str, metric: str) -> Dict[str, np.ndarray]:
    d = np.load(_state_dir(state, metric) / "sensors.npz")
    return {k: d[k] for k in d.files}


@st.cache_data
def load_state_mask(state: str, metric: str) -> np.ndarray:
    return np.load(_state_dir(state, metric) / "state_mask.npz")["mask"]


@st.cache_data
def load_state_density(state: str, metric: str) -> Optional[np.ndarray]:
    for fname in ("population_density.npz", "poverty_density.npz"):
        p = _state_dir(state, metric) / fname
        if p.exists():
            return np.load(p)["density"]
    return None


@st.cache_data
def load_scale_dict() -> dict:
    p = DATA_DIR / "scale_dict.json"
    if not p.exists():
        p = ROOT / "utils" / "scale_dict.json"
    with open(p) as f:
        return json.load(f)


def grid_coords(mask_shape: tuple) -> tuple:
    s = load_scale_dict()
    lats = np.linspace(s["lat"]["min"], s["lat"]["max"], mask_shape[0])
    lons = np.linspace(s["lon"]["min"], s["lon"]["max"], mask_shape[1])
    return lats, lons


# ---------------------------------------------------------------------------
#  Current CPCB network (national)
# ---------------------------------------------------------------------------

@st.cache_data
def load_current_sensors() -> pd.DataFrame:
    """Return a DataFrame of current (pre-optimisation) CPCB station lat/lons."""
    sm = np.load(DATA_DIR / "station_mask.npz")["arr_0"]
    lats, lons = grid_coords(sm.shape)
    lat_idx, lon_idx = np.where(sm)
    return pd.DataFrame({
        "latitude": lats[lat_idx],
        "longitude": lons[lon_idx],
    })


def coverage_gain(proposed: pd.DataFrame) -> dict:
    """Return a cheap 'why better' summary: distance-to-nearest-sensor
    histogram before vs after adding *proposed* sensors.

    Distance is great-circle in km.  Returns a dict with keys:
      'before_km'  — median distance per India grid cell before
      'after_km'   — median distance per India grid cell after
      'bins', 'hist_before', 'hist_after'
    """
    im = np.load(DATA_DIR / "india_mask.npz")["arr_0"]
    sm = np.load(DATA_DIR / "station_mask.npz")["arr_0"]
    lats, lons = grid_coords(im.shape)

    # India grid cells
    lat_idx, lon_idx = np.where(im)
    grid_lat = lats[lat_idx]
    grid_lon = lons[lon_idx]

    cur_lat_idx, cur_lon_idx = np.where(sm)
    cur_lat = lats[cur_lat_idx]
    cur_lon = lons[cur_lon_idx]

    def nn_km(tgt_lat, tgt_lon, src_lat, src_lon):
        # crude equirectangular; good enough for km bins
        t = np.stack([tgt_lat, tgt_lon], axis=1)
        s = np.stack([src_lat, src_lon], axis=1)
        # chunk to keep memory reasonable
        out = np.empty(len(t))
        chunk = 512
        for i in range(0, len(t), chunk):
            d = np.linalg.norm(t[i:i+chunk, None, :] - s[None, :, :], axis=2)
            out[i:i+chunk] = d.min(axis=1) * 111.0  # deg → km (~latitude scale)
        return out

    before = nn_km(grid_lat, grid_lon, cur_lat, cur_lon)

    if proposed is not None and len(proposed) > 0:
        all_lat = np.concatenate([cur_lat, proposed["latitude"].to_numpy()])
        all_lon = np.concatenate([cur_lon, proposed["longitude"].to_numpy()])
    else:
        all_lat, all_lon = cur_lat, cur_lon
    after = nn_km(grid_lat, grid_lon, all_lat, all_lon)

    bins = np.array([0, 20, 50, 100, 200, 400, 2000])
    hist_before, _ = np.histogram(before, bins=bins)
    hist_after, _ = np.histogram(after, bins=bins)

    return {
        "before_km": float(np.median(before)),
        "after_km": float(np.median(after)),
        "mean_before_km": float(before.mean()),
        "mean_after_km": float(after.mean()),
        "bins": bins.tolist(),
        "hist_before": hist_before.tolist(),
        "hist_after": hist_after.tolist(),
        "grid_lat": grid_lat,
        "grid_lon": grid_lon,
        "dist_before": before,
        "dist_after": after,
    }
