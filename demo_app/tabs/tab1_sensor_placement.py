"""
Tab 1: AQ Sensor Placement Visualization
Implements interactive sensor placement with animation and comparison maps.
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from typing import Optional

# Import utilities
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from utils.data_loader import (
    load_sensor_positions, load_trajectory, load_metrics_history, 
    load_district_coverage, load_variance_heatmap, get_k_values, get_methods
)
from utils.map_creator import (
    create_sensor_placement_map, create_choropleth_comparison, create_animation_frame
)
from utils.animation_handler import (
    create_animation_controls, render_metrics_panel, animate_sensor_movement,
    create_step_by_step_viewer
)

def render_tab1():
    """Render the AQ Sensor Placement Visualization tab."""
    
    st.title("🌍 AQ Sensor Placement Visualization")
    st.markdown("Interactive visualization of sensor optimization with animation and comparison.")
    
    # Top Controls
    st.header("⚙️ Configuration")
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        k_sensors = st.selectbox(
            "Number of Sensors (K)",
            options=get_k_values(),
            index=2,  # Default to 200
            help="Select the total number of sensors to deploy"
        )
    
    with col2:
        method = st.selectbox(
            "Optimization Method",
            options=get_methods(),
            index=0,  # Default to MaxVar
            help="Choose the optimization algorithm"
        )
    
    with col3:
        show_animation = st.checkbox(
            "Enable Animation",
            value=False,
            help="Show animated sensor movement"
        )
    
    # Load data based on selections
    with st.spinner("Loading sensor data..."):
        current_sensors, optimized_sensors = load_sensor_positions(k_sensors, method)
        variance, lat_grid, lon_grid = load_variance_heatmap()
        
        if len(current_sensors) == 0 or len(optimized_sensors) == 0:
            st.error(f"No sensor data available for K={k_sensors}, Method={method}")
            return
    
    # Main visualization section
    st.header("📍 Sensor Deployment Map")
    
    if show_animation:
        # Animation mode
        trajectory = load_trajectory(k_sensors, method)
        metrics_history = load_metrics_history()
        
        if len(trajectory) == 0:
            st.error("No animation data available")
        else:
            st.info("🎬 Animation Mode - Watch sensors move from current to optimized positions")
            
            # Animation controls
            animation_type = st.radio(
                "Animation Type",
                ["Auto Play", "Step by Step"],
                horizontal=True
            )
            
            if animation_type == "Auto Play":
                animate_sensor_movement(
                    trajectory, metrics_history, 
                    variance, lat_grid, lon_grid,
                    show_trails=True, show_variance=True
                )
            else:
                create_step_by_step_viewer(
                    trajectory, metrics_history,
                    variance, lat_grid, lon_grid
                )
    else:
        # Static mode
        st.info("📊 Static Mode - Compare current vs optimized sensor placement")
        
        # Display options
        col1, col2 = st.columns(2)
        with col1:
            show_variance_heatmap = st.checkbox("Show Variance Heatmap", value=True)
        with col2:
            show_metrics = st.checkbox("Show Performance Metrics", value=True)
        
        # Create main map
        fig = create_sensor_placement_map(
            current_sensors, optimized_sensors,
            variance, lat_grid, lon_grid,
            show_variance=show_variance_heatmap,
            title=f"Sensor Optimization: {method} Method (K={k_sensors})"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Show metrics if requested
        if show_metrics:
            display_performance_metrics(k_sensors, method)
    
    # Comparison section
    st.header("📊 Method Comparison")
    st.markdown("Compare coverage across different deployment strategies")
    
    # Load district data for comparison
    district_data = load_district_coverage()
    
    if not district_data.empty:
        # Filter options
        col1, col2 = st.columns(2)
        
        with col1:
            available_states = ["All States"] + sorted(district_data['state_name'].unique())
            selected_state = st.selectbox(
                "Filter by State",
                options=available_states,
                help="Show results for specific state or all states"
            )
        
        with col2:
            show_point_overlay = st.checkbox(
                "Show Sensor Points",
                value=False,
                help="Overlay actual sensor locations on the maps"
            )
        
        # Create comparison choropleth maps
        comparison_fig = create_choropleth_comparison(district_data, selected_state)
        st.plotly_chart(comparison_fig, use_container_width=True)
        
        # Display comparison metrics
        display_comparison_metrics(district_data, selected_state)
    else:
        st.error("District comparison data not available")

def display_performance_metrics(k_sensors: int, method: str) -> None:
    """Display performance metrics for current configuration."""
    
    st.subheader("📈 Performance Metrics")
    
    # Generate mock metrics based on k_sensors and method
    np.random.seed(42)  # For consistent demo values
    
    # Base metrics that improve with more sensors
    base_variance_reduction = min(0.8, k_sensors / 5000)  # Max 80% reduction
    method_bonus = 0.1 if method == "GDMI" else 0.0
    
    current_variance = 0.247
    optimized_variance = current_variance * (1 - base_variance_reduction - method_bonus)
    
    current_rmse = 7.89
    optimized_rmse = current_rmse * (1 - base_variance_reduction * 0.6)
    
    current_coverage = 45  # percent
    optimized_coverage = min(95, current_coverage + base_variance_reduction * 60)
    
    # Display metrics in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Variance Loss",
            value=f"{optimized_variance:.3f}",
            delta=f"-{current_variance - optimized_variance:.3f}",
            help="Lower is better"
        )
    
    with col2:
        st.metric(
            label="RMSE",
            value=f"{optimized_rmse:.2f}",
            delta=f"-{current_rmse - optimized_rmse:.2f}",
            help="Root Mean Square Error - Lower is better"
        )
    
    with col3:
        st.metric(
            label="Coverage",
            value=f"{optimized_coverage:.1f}%",
            delta=f"+{optimized_coverage - current_coverage:.1f}%",
            help="Population coverage percentage"
        )
    
    with col4:
        improvement = (current_variance - optimized_variance) / current_variance * 100
        st.metric(
            label="Improvement",
            value=f"{improvement:.1f}%",
            delta=f"+{improvement:.1f}%",
            help="Overall performance improvement"
        )

def display_comparison_metrics(district_data: pd.DataFrame, selected_state: Optional[str]) -> None:
    """Display comparison metrics between different methods."""
    
    # Filter data if state is selected
    if selected_state and selected_state != "All States":
        data = district_data[district_data['state_name'] == selected_state]
    else:
        data = district_data
    
    if data.empty:
        return
    
    st.subheader("📊 Coverage Comparison")
    
    # Calculate average coverage for each method
    current_avg = data['current_coverage'].mean()
    sarath_avg = data['sarath_coverage'].mean()
    proposed_avg = data['proposed_coverage'].mean()
    
    # Calculate sensor counts
    current_sensors = data['current_sensors'].sum()
    sarath_sensors = data['sarath_sensors'].sum()
    proposed_sensors = data['proposed_sensors'].sum()
    
    # Display comparison table
    comparison_df = pd.DataFrame({
        'Method': ['Current Deployment', 'Sarath Method', 'Proposed Method'],
        'Avg Coverage (%)': [f"{current_avg:.1f}", f"{sarath_avg:.1f}", f"{proposed_avg:.1f}"],
        'Total Sensors': [current_sensors, sarath_sensors, proposed_sensors],
        'Coverage per Sensor': [
            f"{current_avg/current_sensors:.2f}" if current_sensors > 0 else "0",
            f"{sarath_avg/sarath_sensors:.2f}" if sarath_sensors > 0 else "0", 
            f"{proposed_avg/proposed_sensors:.2f}" if proposed_sensors > 0 else "0"
        ]
    })
    
    st.dataframe(comparison_df, use_container_width=True)
    
    # Show improvement metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        sarath_improvement = ((sarath_avg - current_avg) / current_avg * 100) if current_avg > 0 else 0
        st.metric(
            "Sarath vs Current",
            value=f"{sarath_improvement:+.1f}%",
            help="Coverage improvement over current deployment"
        )
    
    with col2:
        proposed_improvement = ((proposed_avg - current_avg) / current_avg * 100) if current_avg > 0 else 0
        st.metric(
            "Proposed vs Current", 
            value=f"{proposed_improvement:+.1f}%",
            help="Coverage improvement over current deployment"
        )
    
    with col3:
        best_improvement = ((proposed_avg - sarath_avg) / sarath_avg * 100) if sarath_avg > 0 else 0
        st.metric(
            "Proposed vs Sarath",
            value=f"{best_improvement:+.1f}%", 
            help="Coverage improvement over Sarath method"
        )
    
    # Show geographic distribution
    if len(data['state_name'].unique()) > 1:
        st.subheader("📍 State-wise Breakdown")
        
        state_summary = data.groupby('state_name').agg({
            'current_coverage': 'mean',
            'sarath_coverage': 'mean', 
            'proposed_coverage': 'mean',
            'current_sensors': 'sum',
            'sarath_sensors': 'sum',
            'proposed_sensors': 'sum'
        }).round(2)
        
        st.dataframe(state_summary, use_container_width=True)

if __name__ == "__main__":
    render_tab1()