"""Tab 2: Fairness Aware Placement

Three-column layout:
 - Left:   Baseline (existing sensors only)
 - Centre: GD-MI new sensors (fairness-blind)
 - Right:  Fairness-Aware new sensors (population-weighted)

All maps are Plotly figures with population-density overlay and sensor markers,
built from cached artefacts in ``cache/fairness_data/<State_Name>/``.
"""

import streamlit as st
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))

from utils.tab2_utils import (
    create_plotly_state_map,
    get_cached_states,
    has_cached_data,
    load_fairness_metrics,
)


def render_tab2():
    st.title("⚖️ Fairness Aware Sensor Placement")
    # st.markdown(
    #     "Compare **existing** vs **GD-MI** vs **fairness-aware** sensor deployment, "
    #     "overlaid on population density."
    # )

    # --- Controls ---
    ctrl1, ctrl2 = st.columns(2)
    with ctrl2:
        fairness_metric = st.selectbox(
            "Fairness Metric",
            options=["population", "poverty"],
            format_func=lambda x: {"population": "Population Density", "poverty": "Poverty Rate"}[x],
        )

    cached_states = get_cached_states(fairness_metric)
    if not cached_states:
        st.error(f"No cached data for metric **{fairness_metric}**. Run `fairness-aware.py` first.")
        return

    default_idx = cached_states.index("Madhya Pradesh") if "Madhya Pradesh" in cached_states else 0
    with ctrl1:
        selected_state = st.selectbox("Select State", options=cached_states, index=default_idx)

    if not has_cached_data(selected_state, fairness_metric):
        st.warning(f"No cached data for **{selected_state}** / **{fairness_metric}**. Run the pipeline first.")
        return

    st.divider()

    # --- Maps: three columns ---
    col_left, col_centre, col_right = st.columns(3)

    with col_left:
        st.subheader("Baseline")
        fig_baseline = create_plotly_state_map(
            selected_state, metric=fairness_metric, show_sensors="baseline",
        )
        fig_baseline.update_layout(title=f"{selected_state}: Existing Sensors")
        st.plotly_chart(fig_baseline, use_container_width=True)

    with col_centre:
        st.subheader("Normal GD-MI")
        fig_normal = create_plotly_state_map(
            selected_state, metric=fairness_metric, show_sensors="normal",
        )
        fig_normal.update_layout(title=f"{selected_state}: GD-MI New Sensors")
        st.plotly_chart(fig_normal, use_container_width=True)

    with col_right:
        st.subheader("Fairness-Aware GDMI")
        fig_pop = create_plotly_state_map(
            selected_state, metric=fairness_metric, show_sensors="pop",
        )
        fig_pop.update_layout(title=f"{selected_state}: Fairness-Aware New Sensors")
        st.plotly_chart(fig_pop, use_container_width=True)

    # --- Metrics table ---
    st.divider()
    metrics = load_fairness_metrics(selected_state, fairness_metric)

    baseline = metrics.get("baseline", {})
    normal = metrics.get("normal_gdmi", {})
    pop = metrics.get("pop_weighted_gdmi", {})

    prmse_n = normal.get("pop_rmse", 0)
    prmse_p = pop.get("pop_rmse", 0)

    # Delta: Fair Pop-RMSE vs GD-MI Pop-RMSE
    if prmse_n != 0:
        fair_vs_gdmi_pct = (prmse_n - prmse_p) / prmse_n * 100
        fair_delta_str = f"{fair_vs_gdmi_pct:+.2f}% vs GD-MI"
    else:
        fair_delta_str = None

    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Baseline RMSE", f"{baseline.get('rmse', 0):.4f}")
        st.metric("Baseline Pop-RMSE", f"{baseline.get('pop_rmse', 0):.4f}")
        st.caption(f"Sensors: {metrics.get('n_initial_sensors', '?')}")
    with m2:
        st.metric("GD-MI RMSE", f"{normal.get('rmse', 0):.4f}")
        st.metric("GD-MI Pop-RMSE", f"{prmse_n:.4f}")
        st.caption(f"Sensors: {normal.get('n_total_sensors', '?')} (+{normal.get('n_new_sensors', '?')} new)")
    with m3:
        st.metric("Fair RMSE", f"{pop.get('rmse', 0):.4f}")
        st.metric("Fair Pop-RMSE", f"{prmse_p:.4f}",
                   delta=fair_delta_str, delta_color="normal")
        st.caption(f"Sensors: {pop.get('n_total_sensors', '?')} (+{pop.get('n_new_sensors', '?')} new)")


if __name__ == "__main__":
    render_tab2()