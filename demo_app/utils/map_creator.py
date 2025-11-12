"""
Map creation utilities for the AQS demo application.
Handles creation of interactive maps using Plotly.
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import streamlit as st
from typing import List, Dict, Tuple, Any, Optional

# India geographic bounds
INDIA_BOUNDS = {
    'lat_min': 8, 'lat_max': 37,
    'lon_min': 68, 'lon_max': 97,
    'center_lat': 22.5, 'center_lon': 82.5
}

def create_base_india_map(height: int = 600, title: str = "") -> go.Figure:
    """Create a base India map with proper projection and styling."""
    fig = go.Figure()
    
    fig.update_layout(
        title=dict(
            text=title,
            x=0.5,
            font=dict(size=16, color='#2E86AB')
        ),
        geo=dict(
            projection_type='natural earth',
            showland=True,
            landcolor='rgb(243, 243, 243)',
            coastlinecolor='rgb(204, 204, 204)',
            showlakes=True,
            lakecolor='rgb(255, 255, 255)',
            showsubunits=True,
            subunitcolor='rgb(217, 217, 217)',
            countrycolor='rgb(204, 204, 204)',
            lataxis_range=[INDIA_BOUNDS['lat_min'], INDIA_BOUNDS['lat_max']],
            lonaxis_range=[INDIA_BOUNDS['lon_min'], INDIA_BOUNDS['lon_max']],
            center=dict(lat=INDIA_BOUNDS['center_lat'], lon=INDIA_BOUNDS['center_lon']),
            projection_scale=3
        ),
        height=height,
        margin=dict(l=0, r=0, t=40, b=0)
    )
    
    return fig

def add_sensors_to_map(fig: go.Figure, sensors: np.ndarray, name: str = "Sensors", 
                      color: str = 'red', size: int = 4, symbol: str = 'circle') -> go.Figure:
    """Add sensor points to an existing map."""
    if len(sensors) == 0:
        return fig
    
    fig.add_trace(go.Scattergeo(
        lat=sensors[:, 0],
        lon=sensors[:, 1],
        mode='markers',
        name=name,
        marker=dict(
            size=size,
            color=color,
            symbol=symbol,
            line=dict(width=0.5, color='white')
        ),
        hovertemplate=f"<b>{name}</b><br>" +
                     "Lat: %{lat:.2f}<br>" +
                     "Lon: %{lon:.2f}<extra></extra>"
    ))
    
    return fig

def add_variance_heatmap(fig: go.Figure, variance: np.ndarray, 
                        lat_grid: np.ndarray, lon_grid: np.ndarray,
                        opacity: float = 0.6) -> go.Figure:
    """Add variance heatmap overlay to map."""
    if len(variance) == 0:
        return fig
    
    fig.add_trace(go.Heatmap(
        z=variance,
        x=lon_grid,
        y=lat_grid,
        colorscale='Viridis',
        opacity=opacity,
        showscale=True,
        colorbar=dict(
            title="Variance",
            titleside="right"
        ),
        hovertemplate="Lat: %{y:.1f}<br>Lon: %{x:.1f}<br>Variance: %{z:.3f}<extra></extra>"
    ))
    
    return fig

def create_sensor_placement_map(current_sensors: np.ndarray, optimized_sensors: np.ndarray,
                               variance: np.ndarray, lat_grid: np.ndarray, lon_grid: np.ndarray,
                               show_variance: bool = True, title: str = "") -> go.Figure:
    """Create main sensor placement visualization map."""
    fig = create_base_india_map(height=600, title=title)
    
    # Add variance heatmap if requested
    if show_variance and len(variance) > 0:
        fig = add_variance_heatmap(fig, variance, lat_grid, lon_grid)
    
    # Add current sensors
    if len(current_sensors) > 0:
        fig = add_sensors_to_map(
            fig, current_sensors, 
            name="Current Sensors", 
            color='red', 
            size=6, 
            symbol='circle'
        )
    
    # Add optimized sensors
    if len(optimized_sensors) > 0:
        fig = add_sensors_to_map(
            fig, optimized_sensors, 
            name="Optimized Sensors", 
            color='blue', 
            size=6, 
            symbol='star'
        )
    
    return fig

def create_animation_frame(sensors: np.ndarray, step: int, 
                          variance: np.ndarray, lat_grid: np.ndarray, lon_grid: np.ndarray,
                          show_variance: bool = True) -> go.Figure:
    """Create a single frame for sensor animation."""
    fig = create_base_india_map(height=600, title=f"Sensor Optimization - Step {step}")
    
    # Add variance heatmap
    if show_variance and len(variance) > 0:
        fig = add_variance_heatmap(fig, variance, lat_grid, lon_grid)
    
    # Add sensors at current positions
    if len(sensors) > 0:
        fig = add_sensors_to_map(
            fig, sensors,
            name="Sensors",
            color='orange',
            size=6,
            symbol='circle'
        )
    
    return fig

def create_choropleth_comparison(district_data: pd.DataFrame, 
                                selected_state: Optional[str] = None) -> go.Figure:
    """Create comparison choropleth maps for different methods."""
    if district_data.empty:
        return go.Figure()
    
    # Filter by state if selected
    if selected_state and selected_state != "All States":
        district_data = district_data[district_data['state_name'] == selected_state]
    
    # Create subplot with 3 columns
    fig = make_subplots(
        rows=1, cols=3,
        subplot_titles=["Current Deployment", "Sarath Method", "Proposed Method"],
        specs=[[{"type": "geo"}, {"type": "geo"}, {"type": "geo"}]]
    )
    
    # Helper function to add choropleth
    def add_choropleth(col: int, coverage_col: str, title: str):
        fig.add_trace(
            go.Choropleth(
                locations=district_data['district_name'],
                z=district_data[coverage_col],
                colorscale='RdYlBu_r',
                marker_line_color='darkgray',
                marker_line_width=0.5,
                colorbar=dict(
                    title=f"{title}<br>Coverage %",
                    x=0.2 + (col-1) * 0.4,
                    len=0.7
                ),
                showscale=(col == 2)  # Only show colorbar for middle plot
            ),
            row=1, col=col
        )
    
    add_choropleth(1, 'current_coverage', 'Current')
    add_choropleth(2, 'sarath_coverage', 'Sarath')
    add_choropleth(3, 'proposed_coverage', 'Proposed')
    
    # Update geos for each subplot
    for col in range(1, 4):
        fig.update_geos(
            lataxis_range=[INDIA_BOUNDS['lat_min'], INDIA_BOUNDS['lat_max']],
            lonaxis_range=[INDIA_BOUNDS['lon_min'], INDIA_BOUNDS['lon_max']],
            projection_type='natural earth',
            showland=True,
            landcolor='lightgray',
            row=1, col=col
        )
    
    fig.update_layout(
        height=400,
        title_text="Coverage Comparison Across Methods",
        title_x=0.5
    )
    
    return fig

def create_fairness_maps(fairness_data: Dict[str, Dict], selected_state: Optional[str] = None,
                        fairness_metric: str = 'population', show_overlay: bool = True,
                        show_points: bool = False) -> go.Figure:
    """Create three maps showing different fairness approaches."""
    if not fairness_data:
        return go.Figure()
    
    # Create subplot with 3 columns
    fig = make_subplots(
        rows=1, cols=3,
        subplot_titles=["Current Biased", "Fairness Blind", "Fairness Aware"],
        specs=[[{"type": "geo"}, {"type": "geo"}, {"type": "geo"}]]
    )
    
    # Prepare data for choropleth
    states = list(fairness_data.keys())
    
    # Filter by state if selected
    if selected_state and selected_state != "All States":
        states = [selected_state] if selected_state in states else []
    
    if not states:
        return fig
    
    # Extract metrics
    metric_map = {
        'population': 'population_density',
        'poverty': 'poverty_rate', 
        'gdp': 'gdp_per_capita'
    }
    
    metric_key = metric_map.get(fairness_metric, 'population_density')
    metric_values = [fairness_data[state][metric_key] for state in states]
    
    # Create mock sensor distributions for visualization
    np.random.seed(42)  # For reproducible mock data
    
    for col, approach in enumerate(['current', 'blind', 'fair'], 1):
        # Add fairness overlay if requested
        if show_overlay:
            fig.add_trace(
                go.Choropleth(
                    locations=states,
                    z=metric_values,
                    colorscale='Viridis',
                    marker_line_color='darkgray',
                    marker_line_width=0.5,
                    opacity=0.7,
                    showscale=(col == 1),
                    colorbar=dict(
                        title=f"{fairness_metric.title()}<br>Density",
                        x=-0.1 if col == 1 else None
                    )
                ),
                row=1, col=col
            )
        
        # Add mock sensors if requested
        if show_points and col in [1, 3]:  # Only for current and fair approaches
            # Generate mock sensor positions
            n_sensors = 50 if col == 1 else 100
            sensor_lats = np.random.uniform(INDIA_BOUNDS['lat_min'], INDIA_BOUNDS['lat_max'], n_sensors)
            sensor_lons = np.random.uniform(INDIA_BOUNDS['lon_min'], INDIA_BOUNDS['lon_max'], n_sensors)
            
            if col == 1:  # Current - clustered near metros
                # Bias towards major cities
                sensor_lats = sensor_lats * 0.3 + 0.7 * np.random.choice([28.6, 19.0, 12.9], n_sensors)
                sensor_lons = sensor_lons * 0.3 + 0.7 * np.random.choice([77.2, 72.8, 77.6], n_sensors)
            
            fig.add_trace(
                go.Scattergeo(
                    lat=sensor_lats,
                    lon=sensor_lons,
                    mode='markers',
                    marker=dict(
                        size=4,
                        color='red' if col == 1 else 'blue',
                        symbol='circle'
                    ),
                    name=f"{'Current' if col == 1 else 'Fair'} Sensors",
                    showlegend=(col == 1)
                ),
                row=1, col=col
            )
    
    # Update geos
    for col in range(1, 4):
        fig.update_geos(
            lataxis_range=[INDIA_BOUNDS['lat_min'], INDIA_BOUNDS['lat_max']],
            lonaxis_range=[INDIA_BOUNDS['lon_min'], INDIA_BOUNDS['lon_max']],
            projection_type='natural earth',
            showland=True,
            landcolor='lightgray',
            row=1, col=col
        )
    
    fig.update_layout(
        height=500,
        title_text=f"Fairness Comparison - {fairness_metric.title()} Metric",
        title_x=0.5
    )
    
    return fig

def create_budget_allocation_maps(selected_states: List[str], allocation_data: pd.DataFrame) -> go.Figure:
    """Create budget allocation comparison maps."""
    if allocation_data.empty or not selected_states:
        return go.Figure()
    
    # Create subplot with 3 columns
    fig = make_subplots(
        rows=1, cols=3,
        subplot_titles=["Sarath Allocation", "Independent Optimization", "Cooperative Optimization"],
        specs=[[{"type": "geo"}, {"type": "geo"}, {"type": "geo"}]]
    )
    
    # Filter allocation data for selected states
    state_allocation = allocation_data[allocation_data['state_name'].isin(selected_states)]
    
    if state_allocation.empty:
        return fig
    
    # Create mock optimized allocations
    np.random.seed(42)
    
    for col, method in enumerate(['sarath', 'independent', 'cooperative'], 1):
        if method == 'sarath':
            allocations = state_allocation['required_sensors'].values
        elif method == 'independent':
            # Independent optimization - moderate improvement
            allocations = state_allocation['required_sensors'].values * 1.2
        else:  # cooperative
            # Cooperative optimization - best improvement
            allocations = state_allocation['required_sensors'].values * 1.5
        
        fig.add_trace(
            go.Choropleth(
                locations=state_allocation['state_name'],
                z=allocations,
                colorscale='Blues',
                marker_line_color='darkgray',
                marker_line_width=0.5,
                showscale=(col == 2),
                colorbar=dict(
                    title="Sensors<br>Allocated",
                    x=0.5 if col == 2 else None
                )
            ),
            row=1, col=col
        )
    
    # Update geos
    for col in range(1, 4):
        fig.update_geos(
            lataxis_range=[INDIA_BOUNDS['lat_min'], INDIA_BOUNDS['lat_max']],
            lonaxis_range=[INDIA_BOUNDS['lon_min'], INDIA_BOUNDS['lon_max']],
            projection_type='natural earth',
            showland=True,
            landcolor='lightgray',
            row=1, col=col
        )
    
    fig.update_layout(
        height=500,
        title_text="Budget Allocation Optimization Results",
        title_x=0.5
    )
    
    return fig

def create_interactive_state_selection_map(selected_states: List[str] = None) -> go.Figure:
    """Create interactive map for state selection."""
    if selected_states is None:
        selected_states = []
    
    # Indian states with approximate centroids
    states_data = {
        'state': ['Maharashtra', 'Uttar Pradesh', 'Karnataka', 'Gujarat', 'Tamil Nadu',
                 'Rajasthan', 'West Bengal', 'Madhya Pradesh', 'Bihar', 'Andhra Pradesh'],
        'lat': [19.75, 26.85, 15.32, 23.03, 11.13, 27.02, 22.98, 22.97, 25.10, 15.91],
        'lon': [75.71, 80.95, 75.71, 72.03, 78.66, 74.22, 87.75, 78.66, 85.31, 79.74],
        'selected': [state in selected_states for state in ['Maharashtra', 'Uttar Pradesh', 'Karnataka', 'Gujarat', 'Tamil Nadu',
                    'Rajasthan', 'West Bengal', 'Madhya Pradesh', 'Bihar', 'Andhra Pradesh']]
    }
    
    df = pd.DataFrame(states_data)
    
    fig = create_base_india_map(height=400, title="Click States to Select/Deselect")
    
    # Add state markers
    colors = ['orange' if selected else 'lightblue' for selected in df['selected']]
    
    fig.add_trace(go.Scattergeo(
        lat=df['lat'],
        lon=df['lon'],
        mode='markers+text',
        text=df['state'],
        textposition='top center',
        marker=dict(
            size=15,
            color=colors,
            symbol='circle',
            line=dict(width=2, color='darkblue')
        ),
        name="States",
        hovertemplate="<b>%{text}</b><br>" +
                     "Click to select/deselect<extra></extra>"
    ))
    
    return fig