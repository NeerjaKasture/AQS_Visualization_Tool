"""
Tab 1: AQ Sensor Placement Visualization
Implements interactive sensor placement with animation and comparison maps.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import time

# Import utilities
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

# All data loading now handled by map_creator functions
from utils.tab1_utils import (
    create_plotly_india_map
)
from utils.animation_handler import animate_sensor_movement
from utils.data_loader import load_trajectory, load_metrics_history, load_variance_heatmap
# Animation features removed for simplicity

def render_tab1():
    """Render the AQ Sensor Placement Visualization tab."""
    
    st.title("🌍 AQ Sensor Placement Visualization")
    
    st.info("Using optimization results from TNPD model with measurements from CPCB sensors")
    
    # Simple configuration without data dependencies
    col1, col2 = st.columns(2)
    
    with col1:
        k_sensors = st.selectbox(
            "Sensor Configuration",
            options=["20","50", "100", "500"],
            index=0,
        )
    
    with col2:
        method = st.selectbox(
            "Optimization Method",
            options=[ "GDMI ", "MaxVar"],
            index=0,
        )
    
    # Main visualization section
    st.header("📍 Sensor Deployment Map")
    
    
    col = st.columns(1)
    with col[0]:
        show_pm25_overlay = st.checkbox("Show Overlay", value=True)

    try:
        with st.spinner("Rendering interactive map..."):
            # time.sleep(5)  # simulate loading delay
            fig = create_plotly_india_map(k=int(str(k_sensors).strip()), show_overlay=show_pm25_overlay)
            st.plotly_chart(fig, use_container_width=True)
        st.success("✅ Map loaded successfully!", icon="🌍")
    except Exception as e:
        st.warning(f"⚠️ Could not render Plotly map: {e}")

    
    # Animation section
    st.divider()
    st.subheader("Optimization Animation")
    # Button to reveal animation controls
    if 'show_animation_panel' not in st.session_state:
        st.session_state.show_animation_panel = False


    if st.button("▶️ Play Animation", key="open_anim_btn"):
        st.session_state.show_animation_panel = True

    if st.session_state.get("show_animation_panel", False):
        # Resolve k and method keys for file matching
        try:
            k_val = int(str(k_sensors).strip())
        except Exception:
            st.warning("Invalid sensor count; defaulting to k=50.")
            k_val = 50

        # Animation directory
        anim_dir = (Path(__file__).resolve().parent / "../cache/animations").resolve()
        if not anim_dir.exists():
            st.warning(f"Animations directory not found: {anim_dir}")
        else:
            # Find best matching animation file (GIF or video)
            pattern = f"prediction_error_n{k_val}.*"
            candidates = list(anim_dir.glob(pattern))

            # Fallback: show most recent animation if none match k
            if not candidates:
                candidates = sorted(anim_dir.glob("*.*"), key=lambda p: p.stat().st_mtime, reverse=True)

            if not candidates:
                st.info(f"No animation found in {anim_dir}.")
            else:
                anim_path = candidates[0]
                st.caption(f"🎬 Showing animation: {anim_path.name}")

                # Render based on file extension
                ext = anim_path.suffix.lower()
                with open(anim_path, "rb") as f:
                    data = f.read()
                    if ext in (".mp4", ".webm", ".m4v", ".mov"):
                        st.video(data)
                    elif ext == ".gif":
                        st.image(data, use_container_width=False, width=1000)
                    else:
                        st.info(f"Unsupported animation format: {ext}")

    # Best sensors CSV preview and download
    st.divider()
    st.subheader("Download optimum sensor locations")
        

    n_val = int(str(k_sensors).strip())

    # --- Setup paths ---
    BASE_DIR = Path(__file__).resolve().parent
    cache_dir = BASE_DIR / "../cache/loc_csv"

    # Ensure directory exists
    if not cache_dir.exists():
        st.warning(f"Cache directory not found: {cache_dir}")
    else:
        # --- Find matching CSV(s) ---
        candidates = list(cache_dir.glob(f"best_sensors_{n_val}*.csv"))

        if not candidates:
            st.info(f"No CSV found in {cache_dir} for n={n_val} (expected: best_sensors_{n_val}.csv)")
        else:
            # Pick most recently modified file
            csv_path = sorted(candidates, key=lambda p: p.stat().st_mtime, reverse=True)[0]

            # Load and show preview
            df_preview = pd.read_csv(csv_path)
            st.caption(f"📄 Showing: {csv_path.name}")
            st.dataframe(df_preview.head(50), use_container_width=True, height=300)

            from utils.kml_exporter import dataframe_to_kml

            # Generate KML string
            kml_string = dataframe_to_kml(df_preview, lon_col="longitude", lat_col="latitude")

            # KML download button
            st.download_button(
                label="🌐 Download KML (Google Earth)",
                data=kml_string.encode("utf-8"),
                file_name=f"best_sensors_{n_val}.kml",
                mime="application/vnd.google-earth.kml+xml",
                key=f"download_best_sensors_kml_{n_val}"
            )


    
    # # Summary section
    # st.header("📈 Optimization Summary")
    
    # # Get final summary data
    # summary_data = get_sensor_optimization_data() if get_sensor_optimization_data else None
    # if summary_data:
    #     col1, col2 = st.columns(2)
        
    #     with col1:
    #         st.subheader("📊 Key Metrics")
    #         st.write(f"**Total Sensors Optimized**: {summary_data['num_optimized']}")
    #         st.write(f"**Existing CPCB Sensors**: {summary_data['num_deployed']}")
    #         st.write(f"**Optimization Iteration**: {summary_data['iteration']}")
    #         st.write(f"**Variance Loss**: {summary_data['variance_loss']:.6f}")
    #         if summary_data['rmse'] is not None:
    #             st.write(f"**Prediction RMSE**: {summary_data['rmse']:.4f} μg/m³")
        
    #     with col2:
    #         st.subheader("🎯 Research Impact")
    #         st.write("✅ **Population-aware sensor placement**")
    #         st.write("✅ **Neural network-based optimization (TNPD)**")
    #         st.write("✅ **Real PM2.5 data integration**")
    #         st.write("✅ **Fairness-driven deployment strategy**")
    #         st.write("✅ **Interactive visualization for policy decisions**")
    # else:
    #     st.error("Could not load optimization summary data")

if __name__ == "__main__":
    render_tab1()