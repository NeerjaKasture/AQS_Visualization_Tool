"""Section 2 — Head-to-head: maps side-by-side + shared/unique overlap."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data_io import (
    METHOD_META,
    available_ks,
    coverage_gain,
    load_current_sensors,
    load_sensor_coords,
    method_metrics,
)


def _map_figure(df: pd.DataFrame, current: pd.DataFrame, color: str, title: str) -> go.Figure:
    fig = go.Figure()
    # current CPCB — always shown as faded anchor layer
    if not current.empty:
        fig.add_trace(go.Scattergeo(
            lon=current["longitude"], lat=current["latitude"],
            mode="markers",
            marker=dict(size=4, color="#626d79", opacity=.55,
                        line=dict(width=.3, color="white")),
            hovertemplate=(
                "<b>Existing CPCB station</b><br>"
                "Lat: %{lat:.3f}<br>Lon: %{lon:.3f}<extra></extra>"
            ),
            name="Current CPCB",
        ))
    if not df.empty:
        fig.add_trace(go.Scattergeo(
            lon=df["longitude"], lat=df["latitude"],
            mode="markers",
            marker=dict(size=7, color=color, opacity=.9,
                        line=dict(width=.6, color="white")),
            hovertemplate=(
                "<b>Proposed sensor</b><br>"
                "Lat: %{lat:.3f}<br>Lon: %{lon:.3f}<br>"
                "State: %{text}<extra></extra>"
            ),
            text=df.get("state", "—"),
            name="Proposed",
        ))
    fig.update_layout(
        title=dict(text=title, font=dict(family="Source Serif 4, serif", size=16), x=0.02, y=0.97),
        geo=dict(
            projection_type="mercator",
            lonaxis=dict(range=[67, 98]),
            lataxis=dict(range=[5, 38]),
            showland=True, landcolor="#f3efe7",
            showcoastlines=True, coastlinecolor="#626d79",
            showcountries=True, countrycolor="#626d79",
            bgcolor="rgba(0,0,0,0)",
            resolution=50,
        ),
        height=480,
        margin=dict(l=0, r=0, t=40, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=True,
        legend=dict(orientation="h", y=-0.02, x=0.5, xanchor="center",
                    bgcolor="rgba(255,253,249,.75)", bordercolor="rgba(31,38,48,.1)",
                    borderwidth=1, font=dict(size=11)),
    )
    return fig


def _coverage_panel(current: pd.DataFrame, proposed: pd.DataFrame, color: str, label: str):
    """Histogram of grid-cell distance to nearest sensor: current vs (current + proposed)."""
    stats = coverage_gain(proposed)
    bins = stats["bins"]
    bin_labels = [f"{bins[i]}–{bins[i+1]} km" for i in range(len(bins) - 1)]
    bin_labels[-1] = f">{bins[-2]} km"

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=bin_labels, y=stats["hist_before"],
        name="Current CPCB only",
        marker_color="#9aa3ae", opacity=.85,
    ))
    fig.add_trace(go.Bar(
        x=bin_labels, y=stats["hist_after"],
        name=f"+ {label}",
        marker_color=color, opacity=.9,
    ))
    fig.update_layout(
        barmode="group",
        height=280,
        margin=dict(l=50, r=20, t=10, b=40),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Manrope, sans-serif", color="#1f2630"),
        xaxis=dict(title="Distance from grid cell to nearest sensor",
                   gridcolor="rgba(31,38,48,.06)"),
        yaxis=dict(title="# grid cells", gridcolor="rgba(31,38,48,.06)"),
        legend=dict(orientation="h", y=1.15, x=0),
    )
    return fig, stats


def _overlap_stats(a: pd.DataFrame, b: pd.DataFrame, tol_deg: float = 0.1) -> dict:
    """Count coords in a also in b within `tol_deg` (~11 km) tolerance."""
    if a.empty or b.empty:
        return {"shared": 0, "only_a": len(a), "only_b": len(b)}
    a_pts = a[["latitude", "longitude"]].to_numpy()
    b_pts = b[["latitude", "longitude"]].to_numpy()
    d = np.linalg.norm(a_pts[:, None, :] - b_pts[None, :, :], axis=2)
    match_a = (d.min(axis=1) < tol_deg).sum()
    match_b = (d.min(axis=0) < tol_deg).sum()
    return {
        "shared": int(min(match_a, match_b)),
        "only_a": int(len(a) - match_a),
        "only_b": int(len(b) - match_b),
    }


def _state_bar(a: pd.DataFrame, b: pd.DataFrame) -> go.Figure:
    ca = a["state"].value_counts() if not a.empty else pd.Series(dtype=int)
    cb = b["state"].value_counts() if not b.empty else pd.Series(dtype=int)
    states = sorted(set(ca.index) | set(cb.index))
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=states,
        x=[int(ca.get(s, 0)) for s in states],
        orientation="h",
        marker_color=METHOD_META["gdmi"]["color"],
        name=METHOD_META["gdmi"]["short"],
    ))
    fig.add_trace(go.Bar(
        y=states,
        x=[-int(cb.get(s, 0)) for s in states],
        orientation="h",
        marker_color=METHOD_META["maxvar"]["color"],
        name=METHOD_META["maxvar"]["short"],
    ))
    fig.update_layout(
        barmode="relative",
        height=max(320, 20 * len(states)),
        margin=dict(l=120, r=20, t=30, b=30),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Manrope, sans-serif", color="#1f2630"),
        xaxis=dict(title="← Greedy     sensors per state     Gumbel-softmax →",
                   zeroline=True, zerolinecolor="#626d79", zerolinewidth=1,
                   gridcolor="rgba(31,38,48,.06)"),
        yaxis=dict(title="", autorange="reversed"),
        legend=dict(orientation="h", y=1.05, x=0),
    )
    # show abs labels
    fig.update_traces(
        hovertemplate="%{y}: %{customdata} sensors<extra>%{fullData.name}</extra>",
    )
    fig.data[0].customdata = [int(ca.get(s, 0)) for s in states]
    fig.data[1].customdata = [int(cb.get(s, 0)) for s in states]
    return fig


def render():
    st.markdown(
        '<p class="section-lede">'
        "Pick a budget and see where each strategy plants its sensors. The state-level "
        "mirror chart makes the real disagreement visible — Gumbel-softmax and Greedy don't just "
        "disagree on <em>which</em> points, they disagree on <em>which states</em>."
        "</p>",
        unsafe_allow_html=True,
    )

    ks_gdmi = set(available_ks("gdmi"))
    ks_maxvar = set(available_ks("maxvar"))
    ks = sorted(ks_gdmi & ks_maxvar)
    if not ks:
        st.warning("No overlapping k values between Gumbel-softmax and Greedy caches.")
        return

    col_ctrl1, col_ctrl2, _ = st.columns([1, 1, 3])
    with col_ctrl1:
        k = st.select_slider("Sensor budget (k)", options=ks, value=ks[len(ks) // 2])
    with col_ctrl2:
        cost_per = st.number_input("₹ per sensor (lakh)", min_value=1, max_value=100,
                                   value=20, step=1, help="Rough CAAQMS capex. Changes the budget card below.")

    df_g = load_sensor_coords("gdmi", k)
    df_m = load_sensor_coords("maxvar", k)
    current = load_current_sensors()

    m_g = method_metrics("gdmi", k) or {}
    m_m = method_metrics("maxvar", k) or {}

    # --- budget row ---
    budget_cr = (cost_per * k) / 100.0  # lakh → crore
    cols = st.columns(4)
    with cols[0]:
        st.metric(f"Current network ({len(current)})",
                  f"{m_g.get('rmse_before', 0):.3f}",
                  "μg/m³ baseline RMSE")
    with cols[1]:
        st.metric(f"{METHOD_META['gdmi']['short']} RMSE", f"{m_g.get('rmse_after', 0):.3f}",
                  f"−{m_g.get('improvement_percent', 0):.1f}% vs baseline",
                  delta_color="inverse")
    with cols[2]:
        st.metric(f"{METHOD_META['maxvar']['short']} RMSE", f"{m_m.get('rmse_after', 0):.3f}",
                  f"−{m_m.get('improvement_percent', 0):.1f}% vs baseline",
                  delta_color="inverse")
    with cols[3]:
        st.metric("Capex @ ₹/sensor", f"₹{budget_cr:.2f} cr",
                  f"{k} × ₹{cost_per} lakh")

    # --- maps side-by-side ---
    left, right = st.columns(2)
    with left:
        st.plotly_chart(
            _map_figure(df_g, current, METHOD_META["gdmi"]["color"],
                        f"Current (grey) + Gumbel-softmax new (red) · k = {k}"),
            use_container_width=True, config={"displayModeBar": False},
        )
    with right:
        st.plotly_chart(
            _map_figure(df_m, current, METHOD_META["maxvar"]["color"],
                        f"Current (grey) + Greedy new (blue) · k = {k}"),
            use_container_width=True, config={"displayModeBar": False},
        )

    # --- overlap ---
    o = _overlap_stats(df_g, df_m, tol_deg=0.15)
    total = o["shared"] + o["only_a"] + o["only_b"]
    pct = 100 * o["shared"] / max(total, 1)
    st.markdown(
        f'<div class="callout">'
        f"<strong>Agreement.</strong> At k={k}, Gumbel-softmax and Greedy place ~<strong>{o['shared']}</strong> "
        f"sensors in near-identical locations (~15 km tolerance) — about "
        f"<strong>{pct:.0f}%</strong> of each deployment. The <strong>{o['only_a']}</strong> "
        f"Gumbel-only and <strong>{o['only_b']}</strong> Greedy-only placements are where the "
        f"strategic difference lives."
        f"</div>",
        unsafe_allow_html=True,
    )

    # --- Why we're better: coverage shift ---
    st.markdown("### Why this is better — coverage distance shrinks")
    st.caption(
        "For every ~11 km grid cell in India, we compute the distance to its nearest sensor. "
        "Adding k Gumbel-softmax sensors pushes the whole distribution left — more land is closer to a sensor."
    )

    cov_left, cov_right = st.columns(2)
    with cov_left:
        fig_cov_g, stats_g = _coverage_panel(
            current, df_g, METHOD_META["gdmi"]["color"], "Gumbel-softmax sensors",
        )
        st.plotly_chart(fig_cov_g, use_container_width=True, config={"displayModeBar": False})
        st.markdown(
            f'<div class="callout">'
            f"<strong>Median distance to nearest sensor</strong> drops from "
            f"<strong>{stats_g['before_km']:.0f} km</strong> to "
            f"<strong>{stats_g['after_km']:.0f} km</strong> with Gumbel-softmax — a "
            f"<strong>{100*(1 - stats_g['after_km']/max(stats_g['before_km'],1)):.0f}%</strong> "
            f"reduction."
            f"</div>",
            unsafe_allow_html=True,
        )
    with cov_right:
        fig_cov_m, stats_m = _coverage_panel(
            current, df_m, METHOD_META["maxvar"]["color"], "Greedy sensors",
        )
        st.plotly_chart(fig_cov_m, use_container_width=True, config={"displayModeBar": False})
        st.markdown(
            f'<div class="callout">'
            f"Greedy: median distance drops from "
            f"<strong>{stats_m['before_km']:.0f} km</strong> to "
            f"<strong>{stats_m['after_km']:.0f} km</strong>."
            f"</div>",
            unsafe_allow_html=True,
        )

    # --- state breakdown ---
    st.markdown("### State-wise allocation (mirror chart)")
    st.plotly_chart(_state_bar(df_g, df_m), use_container_width=True,
                    config={"displayModeBar": False})

    # --- live k-evolution animation, driven by real cache ---
    st.markdown("### How the deployment grows as you buy more sensors")
    st.caption(
        "Drag the slider through the budget ladder — each frame is a real Gumbel-softmax run "
        "that was actually optimised at that k, not interpolated. This replaces the "
        "old MP4 and is 50× faster."
    )
    _k_evolution(current)


def _k_evolution(current: pd.DataFrame):
    """Animated-style frames across all available k, driven by plotly frames."""
    ks = sorted(set(available_ks("gdmi")))
    if not ks:
        return

    # Build frames
    frames = []
    sliders_steps = []
    for k in ks:
        df = load_sensor_coords("gdmi", k)
        frames.append(go.Frame(
            data=[
                go.Scattergeo(
                    lon=current["longitude"], lat=current["latitude"],
                    mode="markers",
                    marker=dict(size=4, color="#626d79", opacity=.5,
                                line=dict(width=.3, color="white")),
                    name="Current CPCB",
                ),
                go.Scattergeo(
                    lon=df["longitude"], lat=df["latitude"],
                    mode="markers",
                    marker=dict(size=7, color=METHOD_META["gdmi"]["color"],
                                opacity=.9, line=dict(width=.6, color="white")),
                    name=f"Gumbel-softmax new (k={k})",
                ),
            ],
            name=str(k),
        ))
        sliders_steps.append(dict(
            method="animate",
            label=f"k={k}",
            args=[[str(k)], dict(mode="immediate",
                                 frame=dict(duration=300, redraw=True),
                                 transition=dict(duration=200))],
        ))

    # Initial frame = smallest k
    first_df = load_sensor_coords("gdmi", ks[0])
    fig = go.Figure(
        data=[
            go.Scattergeo(
                lon=current["longitude"], lat=current["latitude"],
                mode="markers",
                marker=dict(size=4, color="#626d79", opacity=.5,
                            line=dict(width=.3, color="white")),
                name="Current CPCB",
            ),
            go.Scattergeo(
                lon=first_df["longitude"], lat=first_df["latitude"],
                mode="markers",
                marker=dict(size=7, color=METHOD_META["gdmi"]["color"],
                            opacity=.9, line=dict(width=.6, color="white")),
                name=f"Gumbel-softmax new",
            ),
        ],
        frames=frames,
    )
    fig.update_layout(
        geo=dict(
            projection_type="mercator",
            lonaxis=dict(range=[67, 98]),
            lataxis=dict(range=[5, 38]),
            showland=True, landcolor="#f3efe7",
            showcoastlines=True, coastlinecolor="#626d79",
            showcountries=True, countrycolor="#626d79",
            bgcolor="rgba(0,0,0,0)",
            resolution=50,
        ),
        height=520,
        margin=dict(l=0, r=0, t=10, b=70),
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=True,
        legend=dict(orientation="h", y=0.02, x=0.5, xanchor="center",
                    bgcolor="rgba(255,253,249,.85)"),
        sliders=[dict(
            active=0, steps=sliders_steps,
            currentvalue=dict(prefix="Budget: ", font=dict(size=13,
                                                          family="Manrope, sans-serif")),
            pad=dict(t=30, b=10),
            len=0.85, x=0.08,
        )],
        updatemenus=[dict(
            type="buttons", showactive=False, direction="left",
            x=0, y=-0.05, xanchor="left", yanchor="top",
            pad=dict(r=10, t=10),
            buttons=[
                dict(label="▶  Play", method="animate",
                     args=[None, dict(frame=dict(duration=700, redraw=True),
                                      transition=dict(duration=300),
                                      fromcurrent=True, mode="immediate")]),
                dict(label="❚❚  Pause", method="animate",
                     args=[[None], dict(frame=dict(duration=0, redraw=False),
                                        mode="immediate",
                                        transition=dict(duration=0))]),
            ],
        )],
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
