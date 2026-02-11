"""
Tab 1: AQ Sensor Placement Visualization
Implements interactive sensor placement with animation and comparison maps.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json
import time

# Import utilities
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

# All data loading now handled by map_creator functions
from utils.tab1_utils import (
    create_plotly_india_map
)

def render_tab1():
    """Render the AQ Sensor Placement Visualization tab."""
    
    st.title("🌍 AQ Sensor Placement Visualization")
    
    st.info("Using optimization results from TNPD model with measurements from CPCB sensors")
    
    # Simple configuration without data dependencies
    col1, col2 = st.columns(2)
    
    with col1:
        k_sensors = st.selectbox(
            "Sensor Configuration",
            options=["20","40", "100", "500"],
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

    # Resolve method key
    method_key = "MaxVar" if "MaxVar" in method else "GDMI"

    try:
        with st.spinner("Rendering interactive map..."):
            # time.sleep(5)  # simulate loading delay
            fig = create_plotly_india_map(k=int(str(k_sensors).strip()), method=method_key, show_overlay=show_pm25_overlay)
            st.plotly_chart(fig, use_container_width=True)
        st.success("✅ Map loaded successfully!", icon="🌍")
    except Exception as e:
        st.warning(f"⚠️ Could not render Plotly map: {e}")

    # --- Optimization Statistics Section ---
    st.divider()
    st.subheader("📊 Metrics")

    summary_path = Path(__file__).resolve().parent / "../cache/vis_data/summary.json"
    try:
        with open(summary_path, "r") as f:
            summary_data = json.load(f)

        # Pick the right section
        section_key = "maxvar" if method_key == "MaxVar" else "gdmi"
        k_str = str(int(str(k_sensors).strip()))
        stats = summary_data.get(section_key, {}).get(k_str)

        if stats is None:
            st.info(f"No statistics available for {method_key} with k={k_str}.")
        else:
            rmse_before = stats.get("rmse_before")
            rmse_after = stats.get("rmse_after")
            improvement_pct = stats.get("improvement_percent")
            pred_rmse = stats.get("pred_rmse")
            final_loss = stats.get("best_loss") or stats.get("final_loss")

            # Metric cards row
            m1, m2 = st.columns(2)
            m1.metric(
                label="RMSE (Existing Sensors)",
                value=f"{rmse_before:.3f} " if rmse_before is not None else "—",
            )
            m2.metric(
                label="RMSE (Post Deployment)",
                value=f"{rmse_after:.3f} " if rmse_after is not None else "—",
                delta=f"-{improvement_pct:.2f}%" if improvement_pct else None,
                delta_color="inverse",
            )
            

            m4, m5 = st.columns(2)
            m4.metric(
                label="Final Predictive RMSE",
                value=f"{pred_rmse:.3f} μg/m³" if pred_rmse is not None else "—",
            )
            m5.metric(
                label="Final Optimization Loss",
                value=f"{final_loss:.6f}" if final_loss is not None else "—",
            )

    except FileNotFoundError:
        st.warning("Summary statistics file not found.")
    except Exception as e:
        st.warning(f"Could not load statistics: {e}")

    
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
            # Find best matching animation file 
            if method_key == "MaxVar":
                pattern = f"prediction_error_maxvar_n{k_val}.gif"
            else:
                pattern = f"prediction_error_n{k_val}.gif"
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
        # --- Find matching CSV(s) based on method ---
        if method_key == "MaxVar":
            candidates = list(cache_dir.glob(f"best_sensors_var_{n_val}*.csv"))
        else:
            candidates = list(cache_dir.glob(f"best_sensors_{n_val}*.csv"))

        if not candidates:
            csv_prefix = f"best_sensors_var_{n_val}" if method_key == "MaxVar" else f"best_sensors_{n_val}"
            st.info(f"No CSV found in {cache_dir} for n={n_val}, method={method_key} (expected: {csv_prefix}.csv)")
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
            kml_filename = f"best_sensors_var_{n_val}.kml" if method_key == "MaxVar" else f"best_sensors_{n_val}.kml"
            st.download_button(
                label="🌐 Download KML (Google Earth)",
                data=kml_string.encode("utf-8"),
                file_name=kml_filename,
                mime="application/vnd.google-earth.kml+xml",
                key=f"download_best_sensors_kml_{n_val}_{method_key}"
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