"""Tab 2: Fairness Aware Placement

Reworked per user request:
 - Dropdowns for state and fairness metric only
 - Two-column layout: Existing (left) vs Proposed Fairness-Aware (right)
 - Each column shows an image loaded from cache/fairness_data
 - RMSE values displayed beneath the images.
"""

import streamlit as st
from pathlib import Path
import sys
from typing import Optional, Tuple

sys.path.append(str(Path(__file__).parent.parent))

from utils.data_loader import (
     get_indian_states
)

BASE_DIR = Path(__file__).resolve().parent
IMAGE_CACHE_DIR = Path(__file__).parent / "../cache/fairness_data"
def _find_image(state: str, metric: str) -> Optional[Path]:
    if not IMAGE_CACHE_DIR.exists():
        return None
    preferred = IMAGE_CACHE_DIR / f"{state}_{metric}.png"
    return preferred

def _metric_key(metric: str) -> str:
    return {
        'population': 'population_density',
        'poverty': 'poverty_rate',
    }[metric]

def render_tab2():
    st.title("⚖️ Fairness Aware Sensor Placement")
    st.markdown("Compare current vs fairness-aware deployment for the selected metric.")

    states_list = get_indian_states()

    col_controls = st.columns(2)
    with col_controls[0]:
        selected_state = st.selectbox("Select State", options=states_list, index=states_list.index("Gujarat") if "Gujarat" in states_list else 0)
    with col_controls[1]:
        fairness_metric = st.selectbox(
            "Fairness Metric",
            options=['population', 'poverty'],
            format_func=lambda x: {
                'population': 'Population Density',
                'poverty': 'Poverty Rate',
            }[x]
        )

    st.divider()

    # Fetch metrics for state
    # state_metrics = fairness_data.get(selected_state, {})
    # current_rmse = state_metrics.get('current_rmse')
    # fair_rmse = state_metrics.get('fair_rmse')
    # current_weighted = state_metrics.get('current_weighted_rmse')
    # fair_weighted = state_metrics.get('fair_weighted_rmse')
    # fairness_score = state_metrics.get('fairness_score')

    # Load images
    existing_img = _find_image(selected_state, 'baseline')
    proposed_img = _find_image(selected_state, fairness_metric)

    col_left, col_right = st.columns(2)
    with col_left:
        st.subheader("Current Deployment")
        if existing_img:
            st.image(str(existing_img), use_container_width=True, caption=f"Existing deployment: {selected_state}")
        else:
            st.warning("No existing image found in cache.")
        # if current_rmse is not None:
        #     st.metric(label="RMSE", value=f"{current_rmse:.2f}")
        # if current_weighted is not None:
        #     st.metric(label="Weighted RMSE", value=f"{current_weighted:.2f}")

    with col_right:
        st.subheader("Fairness-Aware Proposed Deployment")
        if proposed_img:
            st.image(str(proposed_img), use_container_width=True, caption=f"Proposed fairness-aware deployment: {selected_state}")
        else:
            st.warning("No proposed image found in cache.")
        # if fair_rmse is not None:
        #     st.metric(label="RMSE", value=f"{fair_rmse:.2f}")
        # if fair_weighted is not None:
        #     st.metric(label="Weighted RMSE", value=f"{fair_weighted:.2f}")

    # st.divider()
    # # Additional contextual metrics
    # mk = _metric_key(fairness_metric)
    # primary_value = state_metrics.get(mk)
    # if primary_value is not None:
    #     st.info(f"Selected fairness metric ({mk.replace('_',' ')}) value for {selected_state}: {primary_value:.2f}")
    # if fairness_score is not None:
    #     st.caption(f"Fairness score estimate: {fairness_score:.2f}")


if __name__ == "__main__":
    render_tab2()