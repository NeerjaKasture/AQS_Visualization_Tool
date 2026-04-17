"""Section 4 — Fairness: who actually gets covered, at state level."""

from __future__ import annotations

from typing import Tuple

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from data_io import (
    available_fairness_metrics,
    available_states,
    grid_coords,
    load_state_density,
    load_state_mask,
    load_state_metrics,
    load_state_sensors,
)

METRIC_LABEL = {"population": "Population density", "poverty": "Poverty rate"}
METRIC_CSCALE = {"population": "YlGnBu", "poverty": "OrRd"}


def _state_map(state: str, metric: str, show_fair: bool, show_normal: bool) -> go.Figure:
    sensors = load_state_sensors(state, metric)
    mask = load_state_mask(state, metric)
    lats, lons = grid_coords(mask.shape)
    density = load_state_density(state, metric)

    lat_idx, lon_idx = np.where(mask)
    pad = 0.5
    lat_lo, lat_hi = lats[lat_idx.min()] - pad, lats[lat_idx.max()] + pad
    lon_lo, lon_hi = lons[lon_idx.min()] - pad, lons[lon_idx.max()] + pad

    fig = go.Figure()

    if density is not None:
        lmi = (lats >= lat_lo) & (lats <= lat_hi)
        lni = (lons >= lon_lo) & (lons <= lon_hi)
        dc = density[np.ix_(lmi, lni)]
        valid = dc[~np.isnan(dc)]
        vmax = float(np.nanpercentile(valid, 99)) if valid.size else 1.0
        fig.add_trace(go.Heatmap(
            z=dc, x=lons[lni], y=lats[lmi],
            colorscale=METRIC_CSCALE.get(metric, "YlGnBu"),
            zmin=0, zmax=vmax,
            opacity=0.75, showscale=True,
            colorbar=dict(title=METRIC_LABEL.get(metric, metric),
                          x=1.02, thickness=12, len=0.6),
            hovertemplate="lat %{y:.2f}, lon %{x:.2f}<br>value=%{z:.3f}<extra></extra>",
        ))

    fig.add_trace(go.Contour(
        z=mask.astype(float), x=lons, y=lats,
        contours=dict(start=0.5, end=0.5, size=1, coloring="none"),
        line=dict(color="#1f2630", width=1.2),
        hoverinfo="skip", showscale=False,
    ))

    fig.add_trace(go.Scatter(
        x=sensors["old_lon"], y=sensors["old_lat"], mode="markers",
        marker=dict(size=8, color="#1f2630", symbol="circle",
                    line=dict(width=1, color="white")),
        name="Existing sensors",
        hovertemplate="Existing<br>%{y:.2f}, %{x:.2f}<extra></extra>",
    ))
    if show_normal:
        fig.add_trace(go.Scatter(
            x=sensors["normal_new_lon"], y=sensors["normal_new_lat"],
            mode="markers",
            marker=dict(size=10, color="#3c68cf", symbol="diamond",
                        line=dict(width=.8, color="white")),
            name="Gumbel (fairness-blind)",
            hovertemplate="Gumbel<br>%{y:.2f}, %{x:.2f}<extra></extra>",
        ))
    if show_fair:
        fig.add_trace(go.Scatter(
            x=sensors["pop_new_lon"], y=sensors["pop_new_lat"],
            mode="markers",
            marker=dict(size=11, color="#c44536", symbol="star",
                        line=dict(width=.8, color="white")),
            name="Fairness-aware",
            hovertemplate="Fair Gumbel<br>%{y:.2f}, %{x:.2f}<extra></extra>",
        ))

    fig.update_layout(
        height=540,
        margin=dict(l=0, r=0, t=10, b=60),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Manrope, sans-serif", color="#1f2630"),
        xaxis=dict(title="Longitude", range=[lon_lo, lon_hi]),
        yaxis=dict(title="Latitude", range=[lat_lo, lat_hi],
                   scaleanchor="x", scaleratio=1),
        legend=dict(orientation="h", y=-0.1, x=0.5, xanchor="center"),
    )
    return fig


def _coverage_bars(state: str, metric: str) -> Tuple[go.Figure, float, float]:
    """Population / poverty coverage in each decile of the weight raster."""
    sensors = load_state_sensors(state, metric)
    density = load_state_density(state, metric)
    mask = load_state_mask(state, metric)
    if density is None:
        return go.Figure(), 0.0, 0.0

    lats, lons = grid_coords(mask.shape)

    # Weight deciles
    d_flat = density[mask]
    d_valid = d_flat[np.isfinite(d_flat)]
    if d_valid.size == 0:
        return go.Figure(), 0.0, 0.0
    quantiles = np.quantile(d_valid, np.linspace(0, 1, 11))
    quantiles[-1] += 1e-9

    def _sensor_decile_coverage(lon_arr, lat_arr) -> np.ndarray:
        """For each sensor, find which decile cell it sits in.
        Return per-decile count-of-weight-covered."""
        cov = np.zeros(10)
        if len(lon_arr) == 0:
            return cov
        for lo, la in zip(lon_arr, lat_arr):
            # nearest grid cell
            i = int(np.clip(np.searchsorted(lats, la) - 1, 0, len(lats) - 1))
            j = int(np.clip(np.searchsorted(lons, lo) - 1, 0, len(lons) - 1))
            v = density[i, j]
            if not np.isfinite(v):
                continue
            d_idx = int(np.clip(np.searchsorted(quantiles, v) - 1, 0, 9))
            cov[d_idx] += 1
        return cov

    cov_normal = _sensor_decile_coverage(
        np.concatenate([sensors["old_lon"], sensors["normal_new_lon"]]),
        np.concatenate([sensors["old_lat"], sensors["normal_new_lat"]]),
    )
    cov_fair = _sensor_decile_coverage(
        np.concatenate([sensors["old_lon"], sensors["pop_new_lon"]]),
        np.concatenate([sensors["old_lat"], sensors["pop_new_lat"]]),
    )

    deciles = [f"{i*10}–{(i+1)*10}%" for i in range(10)]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=deciles, y=cov_normal, name="Gumbel (blind)",
                         marker_color="#3c68cf", opacity=.85))
    fig.add_trace(go.Bar(x=deciles, y=cov_fair, name="Fairness-aware",
                         marker_color="#c44536", opacity=.9))
    fig.update_layout(
        barmode="group",
        height=320,
        margin=dict(l=40, r=20, t=20, b=40),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Manrope, sans-serif", color="#1f2630"),
        xaxis=dict(title=f"Decile of {METRIC_LABEL.get(metric, metric).lower()} (low → high)",
                   gridcolor="rgba(31,38,48,.06)"),
        yaxis=dict(title="Sensors in decile", gridcolor="rgba(31,38,48,.06)"),
        legend=dict(orientation="h", y=1.12, x=0),
    )
    # High-decile coverage fraction: fraction of sensors in top-5 deciles
    top_frac_fair = cov_fair[5:].sum() / max(cov_fair.sum(), 1)
    top_frac_norm = cov_normal[5:].sum() / max(cov_normal.sum(), 1)
    return fig, top_frac_norm, top_frac_fair


def render():
    st.markdown(
        '<p class="section-lede">'
        "For the states where we have fairness-weighted runs, we can ask: does adding a "
        "population (or poverty) weight to the loss actually shift sensors toward "
        "under-served people? The answer should be visible on both the map and the "
        "decile chart."
        "</p>",
        unsafe_allow_html=True,
    )

    metrics_avail = available_fairness_metrics()
    if not metrics_avail:
        st.warning("No fairness cache found.")
        return

    c1, c2, c3, c4 = st.columns([2, 2, 1, 1])
    with c1:
        metric = st.selectbox("Fairness weight", metrics_avail,
                              format_func=lambda m: METRIC_LABEL.get(m, m))
    states = available_states(metric)
    with c2:
        default_state = "Madhya Pradesh" if "Madhya Pradesh" in states else states[0]
        state = st.selectbox("State", states, index=states.index(default_state))
    with c3:
        show_normal = st.checkbox("Show Gumbel", True)
    with c4:
        show_fair = st.checkbox("Show Fair", True)

    m = load_state_metrics(state, metric)
    base = m.get("baseline", {}) or {}
    norm = m.get("normal_gdmi", {}) or {}
    fair = m.get("pop_weighted_gdmi", {}) or {}

    cols = st.columns(3)
    with cols[0]:
        st.metric("Baseline RMSE", f"{base.get('rmse', 0):.3f}")
        st.caption(f"{m.get('n_initial_sensors', '—')} existing sensors")
    with cols[1]:
        d_rmse = fair.get("rmse", 0) - norm.get("rmse", 0)
        st.metric("RMSE (μg/m³) — fair vs. blind",
                  f"{fair.get('rmse', 0):.3f} vs {norm.get('rmse', 0):.3f}",
                  f"{d_rmse:+.3f}")
    with cols[2]:
        d_prmse = fair.get("pop_rmse", 0) - norm.get("pop_rmse", 0)
        st.metric(f"Weighted RMSE ({metric})",
                  f"{fair.get('pop_rmse', 0):.3f} vs {norm.get('pop_rmse', 0):.3f}",
                  f"{d_prmse:+.3f}", delta_color="inverse")

    st.plotly_chart(
        _state_map(state, metric, show_fair, show_normal),
        use_container_width=True, config={"displayModeBar": False},
    )

    st.markdown("### Coverage by weight decile")
    bars, top_norm, top_fair = _coverage_bars(state, metric)
    st.plotly_chart(bars, use_container_width=True, config={"displayModeBar": False})

    shift = (top_fair - top_norm) * 100
    sign = "more" if shift >= 0 else "fewer"
    st.markdown(
        f'<div class="callout">'
        f"<strong>What changed.</strong> Fairness-aware placement puts "
        f"<strong>{abs(shift):.1f} percentage points {sign}</strong> of its sensors "
        f"in the high-{metric} half of the state, while keeping RMSE nearly unchanged "
        f"({d_rmse:+.3f} μg/m³). The RMSE vs. Pop-RMSE trade-off is small — a cheap way "
        f"to buy policy-relevant coverage."
        f"</div>",
        unsafe_allow_html=True,
    )
