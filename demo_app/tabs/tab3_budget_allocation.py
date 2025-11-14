"""
Tab 3: Budget Constrained Sensor Allocation
Implements interactive state selection and budget optimization comparison.
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import os
from typing import List, Dict, Optional

# Import utilities
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from utils.data_loader import (
    load_allocation_csv, get_indian_states
)
from utils.map_creator import (
    create_interactive_state_selection_map, plot_sensor_choropleth,
    create_base_india_map, add_sensors_to_map
)
from utils.csv_validator import csv_upload_interface

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def render_tab3():
    """Render the Budget Constrained Sensor Allocation tab (dropdown-only selection)."""
    
    st.title("💰 Budget Constrained Sensor Allocation")
    st.markdown("Optimize sensor deployment across states with budget constraints and cooperation strategies.")
    
    # --- Initialize session states ---
    if 'selected_states' not in st.session_state:
        st.session_state.selected_states = []
    if 'allocation_data' not in st.session_state:
        st.session_state.allocation_data = None
    if 'optimization_complete' not in st.session_state:
        st.session_state.optimization_complete = False

    # --- State Selection Section ---
    st.header("🗺️ State Selection")
    st.markdown("Select states from the dropdown to visualize them on the map below.")

    # State selection dropdown
    available_states = get_indian_states()
    selected_states_ui = st.multiselect(
        "Select States",
        options=available_states,
        help="Select or deselect states to visualize and allocate budget"
    )

    # Sync selection immediately (no second click needed)
    st.session_state.selected_states = selected_states_ui

    # --- Display current selection ---
    if st.session_state.selected_states:
        st.success(f"Selected {len(st.session_state.selected_states)} states:")
        st.write(", ".join(st.session_state.selected_states))
    else:
        st.info("ℹ️ No states selected yet.")

    # --- Show live map preview ---
    selection_map = create_interactive_state_selection_map(st.session_state.selected_states)
    st.plotly_chart(selection_map, use_container_width=True)

    # --- Budget Allocation Section ---
    st.header("💸 Budget Allocation Configuration")

    allocation_method = st.selectbox(
        "Select Budget Allocation Method",
        options=["Guttikunda et al. (2019) Allocation", "Repeat Existing Budget", "Upload Custom CSV"],
        help="Choose how to allocate budget across states"
    )
    st.session_state.allocation_method = allocation_method

    # --- Conditionally show CSV uploader ---
    uploaded_csv = None
    if allocation_method == "Upload Custom CSV":
        uploaded_csv = st.file_uploader(
            "Upload Custom Budget Allocation CSV",
            type=["csv"],
            help="Upload a CSV file containing custom state budget allocations."
        )
 
    # --- Handle allocation methods ---
    allocation_df = None
    if allocation_method == "Guttikunda et al. (2019) Allocation":
        allocation_df = load_allocation_csv("sarath")
        if not allocation_df.empty:
            st.success("✅ Loaded Guttikunda et al. (2019) allocation ")
            display_allocation_preview(allocation_df)
        # st.write(allocation_df)
        if st.session_state.selected_states:
            # st.write(st.session_state.selected_states)
            allocation_df = allocation_df[allocation_df['state_name'].isin(st.session_state.selected_states)]
        # st.write(allocation_df)
        
       

    elif allocation_method == "Repeat Existing Budget":
        allocation_df = load_allocation_csv("existing")
        if not allocation_df.empty:
            st.success("✅ Loaded existing budget allocation")
            display_allocation_preview(allocation_df)

    elif allocation_method == "Upload Custom CSV":
        st.markdown("---")
        allocation_df = csv_upload_interface()
        if allocation_df is not None:
            st.success("✅ Custom CSV uploaded successfully")

    if allocation_df is not None:
        st.session_state.allocation_data = allocation_df

    # --- Optimization Section ---
    if st.session_state.selected_states and st.session_state.allocation_data is not None:
        st.header("🚀 Run Optimization")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🎯 Run Budget Optimization", type="primary", use_container_width=True):
                run_budget_optimization()

        if st.session_state.optimization_complete:
            st.header("📊 Optimization Results")
            display_optimization_results()
    else:
        st.header("📋 Requirements")
        st.warning("Please complete the following steps to run optimization:")
        st.write("✅ States selected" if st.session_state.selected_states else "❌ Select states from dropdown")
        st.write("✅ Budget allocation configured" if st.session_state.allocation_data is not None else "❌ Configure budget allocation method")


def display_allocation_preview(allocation_df: pd.DataFrame) -> None:
    """Display preview of allocation data."""
    
    st.subheader("📋 Allocation Preview")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total States", len(allocation_df))
    
    with col2:
        total_sensors = allocation_df['required_sensors'].sum()
        st.metric("Total Sensors", f"{total_sensors:,}")
    
    with col3:
        avg_sensors = allocation_df['required_sensors'].mean()
        st.metric("Avg per State", f"{avg_sensors:.1f}")
    
    # Show top allocations
    with st.expander("View Allocation Details"):
        sorted_allocation = allocation_df.sort_values('required_sensors', ascending=False)
        st.dataframe(sorted_allocation.head(10), use_container_width=True)
        
        if len(allocation_df) > 10:
            st.caption(f"Showing top 10 of {len(allocation_df)} states")

def run_budget_optimization() -> None:
    """Run the budget optimization simulation."""
    
    with st.spinner("🔄 Running optimization algorithms..."):
        # Simulate optimization delay
        import time
        time.sleep(5)
        
        # Mark optimization as complete
        st.session_state.optimization_complete = True
        
        st.success("🎉 Optimization complete! Results are ready below.")

ALLOCATION_COMPARISON_MAP = {
    "Guttikunda et al. (2019) Allocation": (os.path.abspath(os.path.join(BASE_DIR, "..", "cache_tab3", "UttarPradeshMadhyaPradeshRajasthancoords", "independent_sarath.csv")),os.path.abspath(os.path.join(BASE_DIR, "..", "cache_tab3", "UttarPradeshMadhyaPradeshRajasthancoords", "blockwise_sarath.csv"))),
    "Repeat Existing Budget": (os.path.abspath(os.path.join(BASE_DIR, "..", "cache_tab3", "UttarPradeshMadhyaPradeshRajasthancoords", "independent_existing.csv")),os.path.abspath(os.path.join(BASE_DIR, "..", "cache_tab3", "UttarPradeshMadhyaPradeshRajasthancoords", "blockwise_existing.csv"))),
    "Upload Custom CSV": ("custom_run1.csv", "custom_run2.csv"),
}

def display_optimization_results() -> None:
    """Display the optimization results and comparison."""
    
    selected_states = st.session_state.selected_states
    allocation_data = st.session_state.allocation_data
    # Choose the two CSVs (or any other arguments)
    csv_1, csv_2 = ALLOCATION_COMPARISON_MAP[st.session_state.allocation_method]

    # Produce two figures
    fig1 = plot_sensor_choropleth(
        csv_path=f"{csv_1}",
        geojson_path=(os.path.abspath(os.path.join(BASE_DIR, "..", "cache_tab3","INDIA_DISTRICTS.geojson"))),
        state_shapefile_path=(os.path.abspath(os.path.join(BASE_DIR, "..", "cache_tab3","India_State_Boundary.shp")))
    )

    fig2 = plot_sensor_choropleth(
        csv_path=f"{csv_2}",
        geojson_path=(os.path.abspath(os.path.join(BASE_DIR, "..", "cache_tab3","INDIA_DISTRICTS.geojson"))),
        state_shapefile_path=(os.path.abspath(os.path.join(BASE_DIR, "..", "cache_tab3","India_State_Boundary.shp")))
    )

    # Display side by side
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Independent Optimization")
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        st.subheader("Block-wise Cooperative Optimization")
        st.plotly_chart(fig2, use_container_width=True)
 

if __name__ == "__main__":
    render_tab3()