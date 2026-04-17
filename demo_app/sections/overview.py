"""Section 1 — Overview: the story, in real numbers."""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from data_io import (
    METHOD_META,
    comparison_table,
    load_current_sensors,
    load_summary,
)
from theme import callout, num_card


def _headline_numbers():
    summary = load_summary()
    best_gdmi_k = max((int(k) for k in summary.get("gdmi", {})), default=None)
    best = summary.get("gdmi", {}).get(str(best_gdmi_k), {}) if best_gdmi_k else {}
    baseline_rmse = best.get("rmse_before", 0.0)
    fair_rmse = best.get("rmse_after", 0.0)
    improv = best.get("improvement_percent", 0.0)
    n_current = len(load_current_sensors())

    cards = [
        num_card(f"{n_current}", "CPCB stations today"),
        num_card(f"{baseline_rmse:.2f}", "Baseline RMSE (μg/m³)"),
        num_card(f"{fair_rmse:.2f}", f"Gumbel-softmax @ k={best_gdmi_k} (μg/m³)", "accent"),
        num_card(f"−{improv:.1f}%", "Error reduction", "green"),
    ]
    st.markdown('<div class="card-grid">' + "".join(cards) + "</div>", unsafe_allow_html=True)


def _current_network_map():
    df = load_current_sensors()
    fig = go.Figure()
    fig.add_trace(go.Scattergeo(
        lon=df["longitude"], lat=df["latitude"],
        mode="markers",
        marker=dict(size=5, color="#1f2630", opacity=.7,
                    line=dict(width=.4, color="white")),
        hovertemplate="CPCB station<br>%{lat:.2f}, %{lon:.2f}<extra></extra>",
        name="Current CPCB",
    ))
    fig.update_layout(
        height=380,
        margin=dict(l=0, r=0, t=10, b=10),
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
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )
    return fig


def _pareto_plot():
    df = comparison_table()
    if df.empty:
        st.info("No precomputed metrics available.")
        return

    fig = go.Figure()
    for method_key, meta in METHOD_META.items():
        sub = df[df["method_key"] == method_key].sort_values("k")
        if sub.empty:
            continue
        fig.add_trace(go.Scatter(
            x=sub["k"],
            y=sub["rmse_after"],
            mode="lines+markers+text",
            line=dict(color=meta["color"], width=2.5),
            marker=dict(size=11, color=meta["color"], line=dict(width=1.5, color="white")),
            text=[f"k={int(k)}" for k in sub["k"]],
            textposition="top center",
            textfont=dict(size=10, color="#626d79"),
            name=meta["label"],
            hovertemplate=(
                "<b>%{fullData.name}</b><br>"
                "k = %{x}<br>"
                "RMSE = %{y:.3f} μg/m³<extra></extra>"
            ),
        ))

    baseline = df["rmse_before"].dropna().max() if not df.empty else None
    if baseline:
        fig.add_hline(
            y=baseline, line_dash="dot", line_color="#626d79", line_width=1.5,
            annotation_text=f"Baseline (no new sensors) = {baseline:.2f}",
            annotation_position="top left",
            annotation_font_size=11,
            annotation_font_color="#626d79",
        )

    fig.update_layout(
        xaxis=dict(
            title="Number of new sensors (k)",
            type="log", dtick="D1",
            gridcolor="rgba(31,38,48,.06)", zeroline=False,
        ),
        yaxis=dict(
            title="Held-out RMSE (μg/m³, lower = better)",
            gridcolor="rgba(31,38,48,.06)", zeroline=False,
        ),
        height=460,
        margin=dict(l=60, r=30, t=30, b=60),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Manrope, sans-serif", color="#1f2630"),
        legend=dict(
            orientation="h", y=1.08, x=0, yanchor="bottom", xanchor="left",
            bgcolor="rgba(0,0,0,0)",
        ),
        hoverlabel=dict(bgcolor="white", bordercolor="#c44536", font_family="Manrope"),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def _headtohead_table():
    df = comparison_table()
    if df.empty:
        return

    display = df[["strategy", "k", "rmse_before", "rmse_after",
                  "improvement_pct", "pred_rmse", "n_runs"]].copy()
    display.columns = [
        "Strategy", "k sensors", "Baseline RMSE", "After RMSE",
        "Improvement", "Predictive RMSE", "Runs aggregated",
    ]
    display["Baseline RMSE"] = display["Baseline RMSE"].map(lambda v: f"{v:.3f}" if v else "—")
    display["After RMSE"] = display["After RMSE"].map(lambda v: f"{v:.3f}" if v else "—")
    display["Improvement"] = display["Improvement"].map(
        lambda v: f"−{v:.1f}%" if v else "—"
    )
    display["Predictive RMSE"] = display["Predictive RMSE"].map(
        lambda v: f"{v:.3f}" if v else "—"
    )

    st.dataframe(
        display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "k sensors": st.column_config.NumberColumn(width="small"),
            "Runs aggregated": st.column_config.NumberColumn(
                help="Number of independent optimisation runs aggregated", width="small",
            ),
        },
    )


def render():
    st.markdown(
        '<p class="section-lede">'
        "Two placement strategies — <em>Gumbel-softmax</em> (gradient-descent on mutual information, GD-MI) "
        "and <em>Greedy</em> (maximum-variance, MaxVar) — evaluated against the existing "
        "CPCB network on held-out PM<sub>2.5</sub> stations. Numbers below are real, "
        "not simulated."
        "</p>",
        unsafe_allow_html=True,
    )

    _headline_numbers()

    col_map, col_text = st.columns([3, 2])
    with col_map:
        st.markdown("### Where the CPCB network lives today")
        st.plotly_chart(_current_network_map(), use_container_width=True,
                        config={"displayModeBar": False})
    with col_text:
        st.markdown(
            '<div class="callout" style="margin-top:2.5rem">'
            "<strong>The coverage problem.</strong> The ~250 CPCB stations "
            "cluster in Delhi-NCR, Mumbai, Bengaluru, Hyderabad and a handful of "
            "tier-1 cities. Whole districts in the Indo-Gangetic plain — where "
            "PM<sub>2.5</sub> peaks — have <em>no</em> station within 100 km. "
            "Every strategy on the Compare tab has to work <em>on top of</em> this "
            "uneven starting point."
            "</div>",
            unsafe_allow_html=True,
        )

    st.markdown("### RMSE vs. number of new sensors")
    _pareto_plot()

    st.markdown(
        callout(
            "<strong>Reading the plot.</strong> Gumbel-softmax keeps winning at every budget — the "
            "gap widens at larger k because it jointly optimises all sensor positions, "
            "while the greedy baseline commits one sensor at a time. Both decisively beat the existing "
            "network of ~250 CPCB stations."
        ),
        unsafe_allow_html=True,
    )

    with st.expander("See the full comparison table"):
        _headtohead_table()
