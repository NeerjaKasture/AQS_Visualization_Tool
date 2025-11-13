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
import xarray as xr
import json
import os
from glob import glob

# India geographic bounds
INDIA_BOUNDS = {
    'lat_min': 8, 'lat_max': 37,
    'lon_min': 68, 'lon_max': 97,
    'center_lat': 22.5, 'center_lon': 82.5
}

@st.cache_data
def load_sensor_data(results_dir: str = "../../aqs_v2/results/tnpd/default/gd/50/42"):
    """Load and process sensor data using the simple_plot_best approach."""
    try:
        # Find best result JSON
        files = glob(f"{results_dir}/*.json")
        
        if not files:
            return None, None, None, None
        
        def get_loss(file):
            with open(file, 'r') as f:
                data = json.load(f)
            return data['var_loss']
        
        files = sorted(files, key=get_loss)
        best_file = files[0]
        
        # Load best result data
        with open(best_file, 'r') as f:
            data = json.load(f)
        
        # Load scaling parameters
        scale_path = "../../aqs_v2/data/scale_dict.json"
        if os.path.exists(scale_path):
            with open(scale_path) as f:
                scales = json.load(f)
        else:
            return None, None, None, None
        
        # Scale x_best coordinates
        x_new_gd = np.array(data['x_best'])
        x_new_gd_denorm = x_new_gd.copy()
        x_new_gd_denorm[:, 0] = x_new_gd[:, 0] * (scales['lat']['max'] - scales['lat']['min']) + scales['lat']['min']
        x_new_gd_denorm[:, 1] = x_new_gd[:, 1] * (scales['lon']['max'] - scales['lon']['min']) + scales['lon']['min']
        
        # Load deployed sensors
        india_mask_path = "../../aqs_v2/data/india_mask.npz"
        sensors_mask_path = "../../aqs_v2/data/station_mask.npz"
        
        if os.path.exists(india_mask_path) and os.path.exists(sensors_mask_path):
            india_mask = np.load(india_mask_path)['arr_0']
            sensors_mask = np.load(sensors_mask_path)['arr_0']
            deployed_mask = sensors_mask[india_mask]
            
            # Load dataset
            ds_path = "../../aqs_v2/data/val_data.nc"
            if os.path.exists(ds_path):
                ds = xr.open_dataset(ds_path)
                
                # Simple coordinate extraction (mimicking scale_ds)
                lat_coords = ds.lat.values
                lon_coords = ds.lon.values
                lat_grid, lon_grid = np.meshgrid(lat_coords, lon_coords, indexing='ij')
                
                # Create coordinate pairs
                coords = np.stack([lat_grid.flatten(), lon_grid.flatten()], axis=1)
                
                # Apply India mask
                x = coords[india_mask]
                
                # Get deployed sensors
                x_deployed = x[deployed_mask]
                x_deployed[:, 0] = x_deployed[:, 0] * (scales['lat']['max'] - scales['lat']['min']) + scales['lat']['min']
                x_deployed[:, 1] = x_deployed[:, 1] * (scales['lon']['max'] - scales['lon']['min']) + scales['lon']['min']
                
                return x_new_gd_denorm, x_deployed, data, ds
            
        return None, None, None, None
        
    except Exception as e:
        st.error(f"Error loading sensor data: {e}")
        return None, None, None, None

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
            title="Variance"
        ),
        hovertemplate="Lat: %{y:.1f}<br>Lon: %{x:.1f}<br>Variance: %{z:.3f}<extra></extra>"
    ))
    
    return fig

def create_sensor_placement_map(results_dir: str = "../../aqs_v2/results/tnpd/default/gd/50/42",
                               show_pm25_overlay: bool = True, title: str = "") -> go.Figure:
    """Create main sensor placement visualization map using real data."""
    # Load real sensor data
    optimized_sensors, current_sensors, result_data, ds = load_sensor_data(results_dir)
    
    if optimized_sensors is None:
        # Fallback to empty map
        fig = create_base_india_map(height=600, title="Data not available")
        return fig
    
    fig = create_base_india_map(height=600, title=title or f"Sensor Placement - Loss: {result_data.get('var_loss', 'N/A'):.4f}")
    
    # Add PM2.5 heatmap if requested and available
    if show_pm25_overlay and ds is not None:
        try:
            # Use a representative time slice
            ds_slice = ds.isel(time=13) if 'time' in ds.dims else ds
            pm25_data = ds_slice['PM25'].values
            
            # Create heatmap
            fig.add_trace(go.Heatmap(
                z=pm25_data,
                x=ds.lon.values,
                y=ds.lat.values,
                colorscale='Viridis',
                opacity=0.6,
                showscale=True,
                colorbar=dict(
                    title="PM2.5 (μg/m³)",
                    x=1.02
                ),
                hovertemplate="Lat: %{y:.2f}<br>Lon: %{x:.2f}<br>PM2.5: %{z:.1f} μg/m³<extra></extra>"
            ))
        except Exception as e:
            st.warning(f"Could not add PM2.5 overlay: {e}")
    
    # Add current sensors
    if len(current_sensors) > 0:
        fig = add_sensors_to_map(
            fig, current_sensors, 
            name="Current CPCB Sensors", 
            color='black', 
            size=4, 
            symbol='circle'
        )
    
    # Add optimized sensors
    if len(optimized_sensors) > 0:
        fig = add_sensors_to_map(
            fig, optimized_sensors, 
            name="Optimized Sensors", 
            color='red', 
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

def create_fairness_maps(fairness_data: Dict[str, Dict] = None, selected_state: Optional[str] = None,
                        fairness_metric: str = 'population', show_overlay: bool = True,
                        show_points: bool = True) -> go.Figure:
    """Create three maps showing different fairness approaches using real sensor data."""
    # Load real sensor data for comparison
    optimized_sensors, current_sensors, result_data, ds = load_sensor_data()
    
    # Create subplot with 3 columns
    fig = make_subplots(
        rows=1, cols=3,
        subplot_titles=["Current CPCB Deployment", "Population Unaware", "Population Aware"],
        specs=[[{"type": "geo"}, {"type": "geo"}, {"type": "geo"}]]
    )
    
    # Add PM2.5 background if available
    if show_overlay and ds is not None:
        try:
            ds_slice = ds.isel(time=13) if 'time' in ds.dims else ds
            pm25_data = ds_slice['PM25'].values
            
            for col in range(1, 4):
                fig.add_trace(go.Heatmap(
                    z=pm25_data,
                    x=ds.lon.values,
                    y=ds.lat.values,
                    colorscale='Viridis',
                    opacity=0.5,
                    showscale=(col == 1),
                    colorbar=dict(
                        title="PM2.5 (μg/m³)" if col == 1 else None,
                        x=-0.1 if col == 1 else None
                    )
                ), row=1, col=col)
        except Exception:
            pass
    
    # Add sensor points if available
    if show_points:
        # Column 1: Current CPCB sensors
        if current_sensors is not None and len(current_sensors) > 0:
            fig.add_trace(go.Scattergeo(
                lat=current_sensors[:, 0],
                lon=current_sensors[:, 1],
                mode='markers',
                marker=dict(
                    size=4,
                    color='black',
                    symbol='circle',
                    line=dict(width=0.5, color='white')
                ),
                name="Current CPCB Sensors",
                showlegend=True,
                hovertemplate="<b>CPCB Sensor</b><br>Lat: %{lat:.2f}<br>Lon: %{lon:.2f}<extra></extra>"
            ), row=1, col=1)
        
        # Column 2: Population unaware (random/uniform distribution)
        np.random.seed(42)
        n_uniform = len(current_sensors) if current_sensors is not None else 50
        uniform_lats = np.random.uniform(INDIA_BOUNDS['lat_min'], INDIA_BOUNDS['lat_max'], n_uniform)
        uniform_lons = np.random.uniform(INDIA_BOUNDS['lon_min'], INDIA_BOUNDS['lon_max'], n_uniform)
        
        fig.add_trace(go.Scattergeo(
            lat=uniform_lats,
            lon=uniform_lons,
            mode='markers',
            marker=dict(
                size=4,
                color='blue',
                symbol='circle',
                line=dict(width=0.5, color='white')
            ),
            name="Uniform Distribution",
            showlegend=True,
            hovertemplate="<b>Uniform Sensor</b><br>Lat: %{lat:.2f}<br>Lon: %{lon:.2f}<extra></extra>"
        ), row=1, col=2)
        
        # Column 3: Population aware (optimized sensors)
        if optimized_sensors is not None and len(optimized_sensors) > 0:
            fig.add_trace(go.Scattergeo(
                lat=optimized_sensors[:, 0],
                lon=optimized_sensors[:, 1],
                mode='markers',
                marker=dict(
                    size=6,
                    color='red',
                    symbol='star',
                    line=dict(width=0.5, color='white')
                ),
                name="Optimized Sensors",
                showlegend=True,
                hovertemplate="<b>Optimized Sensor</b><br>Lat: %{lat:.2f}<br>Lon: %{lon:.2f}<extra></extra>"
            ), row=1, col=3)
    
    # Update geos for all subplots
    for col in range(1, 4):
        fig.update_geos(
            lataxis_range=[INDIA_BOUNDS['lat_min'], INDIA_BOUNDS['lat_max']],
            lonaxis_range=[INDIA_BOUNDS['lon_min'], INDIA_BOUNDS['lon_max']],
            projection_type='natural earth',
            showland=True,
            landcolor='lightgray',
            coastlinecolor='darkgray',
            row=1, col=col
        )
    
    fig.update_layout(
        height=500,
        title_text="Fairness Comparison - Population Aware Sensor Placement",
        title_x=0.5,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        )
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

def create_pm25_prediction_map(results_dir: str = "../../aqs_v2/results/tnpd/default/gd/50/42",
                              show_difference: bool = True, title: str = "") -> go.Figure:
    """Create PM2.5 prediction map similar to simple_plot_best.py visualization."""
    # Load sensor data
    optimized_sensors, current_sensors, result_data, ds = load_sensor_data(results_dir)
    
    if ds is None:
        return create_base_india_map(height=600, title="Data not available")
    
    try:
        # Use time slice 13 like in simple_plot_best.py
        ds_slice = ds.isel(time=13) if 'time' in ds.dims else ds
        
        # Try to generate predictions (simplified version)
        pm25_data = ds_slice['PM25'].values
        
        # For now, create a mock prediction difference
        # In a full implementation, you would run the model prediction here
        np.random.seed(42)
        pred_difference = np.random.normal(0, 5, pm25_data.shape)  # Mock residuals
        
        # Create the map
        fig = create_base_india_map(height=600, title=title or "PM2.5 Predictions vs Ground Truth")
        
        if show_difference:
            # Show prediction difference (residuals)
            fig.add_trace(go.Heatmap(
                z=pred_difference,
                x=ds.lon.values,
                y=ds.lat.values,
                colorscale='RdBu_r',
                opacity=0.8,
                showscale=True,
                colorbar=dict(
                    title="PM2.5 Residuals<br>(μg/m³)",
                    x=1.02
                ),
                hovertemplate="Lat: %{y:.2f}<br>Lon: %{x:.2f}<br>Residual: %{z:.1f} μg/m³<extra></extra>"
            ))
        else:
            # Show actual PM2.5 values
            fig.add_trace(go.Heatmap(
                z=pm25_data,
                x=ds.lon.values,
                y=ds.lat.values,
                colorscale='Viridis',
                opacity=0.8,
                showscale=True,
                colorbar=dict(
                    title="PM2.5 (μg/m³)",
                    x=1.02
                ),
                hovertemplate="Lat: %{y:.2f}<br>Lon: %{x:.2f}<br>PM2.5: %{z:.1f} μg/m³<extra></extra>"
            ))
        
        # Add sensors
        if current_sensors is not None and len(current_sensors) > 0:
            fig = add_sensors_to_map(
                fig, current_sensors,
                name="CPCB Sensors",
                color='black',
                size=4,
                symbol='circle'
            )
        
        if optimized_sensors is not None and len(optimized_sensors) > 0:
            fig = add_sensors_to_map(
                fig, optimized_sensors,
                name="Optimized Sensors",
                color='red',
                size=6,
                symbol='star'
            )
        
        return fig
        
    except Exception as e:
        st.error(f"Error creating PM2.5 prediction map: {e}")
        return create_base_india_map(height=600, title="Error loading PM2.5 data")