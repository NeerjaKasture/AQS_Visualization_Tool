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
    "lat_min": 6.0,
    "lat_max": 37.5,
    "lon_min": 68.0,
    "lon_max": 97.5,
    "center_lat": 22.0,
    "center_lon": 79.0,
}
import geopandas as gpd
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import json
def plot_sensor_choropleth(csv_path, geojson_path, state_shapefile_path):
    # ------------------------------
    # Load Data
    # ------------------------------
    sensors_df = pd.read_csv(csv_path)
    districts_gdf = gpd.read_file(geojson_path)
    states_gdf = gpd.read_file(state_shapefile_path)
    states_gdf.rename(columns={"State_Name": "stname"}, inplace=True)

    # Normalize
    sensors_df.columns = sensors_df.columns.str.lower()
    districts_gdf.columns = districts_gdf.columns.str.lower()
    states_gdf.columns = states_gdf.columns.str.lower()

    districts_gdf["stname"] = districts_gdf["stname"].str.strip().str.upper()
    districts_gdf["dtname"] = districts_gdf["dtname"].str.strip().str.upper()

    sensors_df["stname"] = sensors_df["stname"].str.strip().str.upper()
    sensors_df["dtname"] = sensors_df["dtname"].str.strip().str.upper()

    # ------------------------------
    # Count sensors per district
    # ------------------------------
    sensor_counts = (
        sensors_df.groupby(["stname", "dtname"])
        .size()
        .reset_index(name="monitors")
    )

    # ------------------------------
    # Merge counts into district geojson
    # ------------------------------
    merged_gdf = districts_gdf.merge(
        sensor_counts,
        on=["stname", "dtname"],
        how="left"
    )

    merged_gdf["monitors"] = merged_gdf["monitors"].fillna(0).astype(int)

    # ------------------------------
    # Filter only states in CSV
    # ------------------------------
    selected_states = sorted(list(sensor_counts["stname"].unique()))
    filtered_gdf = merged_gdf[merged_gdf["stname"].isin(selected_states)]

    filtered_gdf = filtered_gdf.reset_index(drop=True)
    filtered_gdf["district_id"] = filtered_gdf.index.astype(str)

    # ------------------------------
    # Compute centroids
    # ------------------------------
    india_crs = "EPSG:7755"
    proj = filtered_gdf.to_crs(india_crs)
    proj["centroid"] = proj.geometry.centroid

    centroids_ll = proj.set_geometry("centroid").to_crs("EPSG:4326")
    filtered_gdf["centroid_lon"] = centroids_ll.geometry.x
    filtered_gdf["centroid_lat"] = centroids_ll.geometry.y

    # ------------------------------
    # Convert GeoDataFrame to GeoJSON
    # ------------------------------
    filtered_geojson = json.loads(filtered_gdf.to_json())

    # Map center
    minx, miny, maxx, maxy = filtered_gdf.total_bounds
    center_lat = (miny + maxy) / 2
    center_lon = (minx + maxx) / 2

    # ------------------------------
    # Choropleth MAPBOX
    # ------------------------------
    fig = px.choropleth_mapbox(
        filtered_gdf,
        geojson=filtered_geojson,
        locations="district_id",
        featureidkey="properties.district_id",
        color="monitors",
        color_continuous_scale="Ice_r",
        hover_name="dtname",
        hover_data={"stname": True, "monitors": True, "district_id": False},
        center={"lat": center_lat, "lon": center_lon},
        zoom=5.3,
        opacity=0.6,
        mapbox_style="carto-positron",
    )

    # ------------------------------
    # Add text labels
    # ------------------------------
    fig.add_scattermapbox(
        lon=filtered_gdf["centroid_lon"],
        lat=filtered_gdf["centroid_lat"],
        mode="text",
        text=filtered_gdf["monitors"].astype(str),
        textfont=dict(size=11, color="black"),
        hoverinfo="skip",
        showlegend=False,
    )

    # ------------------------------
    # Add thick state borders
    # ------------------------------
    states_gdf["stname"] = states_gdf["stname"].str.strip().str.upper()
    selected_states_gdf = states_gdf[states_gdf["stname"].isin(selected_states)]
    selected_states_gdf = selected_states_gdf.to_crs("EPSG:4326")

    for _, row in selected_states_gdf.iterrows():
        geom = row.geometry
        if geom.geom_type == "Polygon":
            xs, ys = geom.exterior.xy
            fig.add_scattermapbox(
                lon=list(xs),
                lat=list(ys),
                mode="lines",
                line=dict(width=2, color="black"),
                hoverinfo="skip",
                showlegend=False,
            )
        elif geom.geom_type == "MultiPolygon":
            for poly in geom.geoms:
                xs, ys = poly.exterior.xy
                fig.add_scattermapbox(
                    lon=list(xs),
                    lat=list(ys),
                    mode="lines",
                    line=dict(width=2, color="black"),
                    hoverinfo="skip",
                    showlegend=False,
                )

    fig.update_layout(
        title=dict(
            text=f"_",
            x=0.5,
            xanchor="center",
        ),
        margin=dict(l=0, r=0, t=40, b=0),
        height=750,
    )

    return fig


def create_base_india_map(height: int = 600, title: str = "") -> go.Figure:
    """Create a base map focused on India with proper zoom, pan, and framing."""
    fig = go.Figure()

    fig.update_layout(
        title=dict(
            text=title,
            x=0.5,
            font=dict(size=16, color="#2E86AB")
        ),
        geo=dict(
            projection_type="mercator",
            showland=True,
            landcolor="rgb(243, 243, 243)",
            coastlinecolor="rgb(150, 150, 150)",
            showlakes=True,
            lakecolor="rgb(255, 255, 255)",
            showcountries=True,
            countrycolor="rgb(150, 150, 150)",
            lataxis_range=[INDIA_BOUNDS["lat_min"], INDIA_BOUNDS["lat_max"]],
            lonaxis_range=[INDIA_BOUNDS["lon_min"], INDIA_BOUNDS["lon_max"]],
            center=dict(lat=INDIA_BOUNDS["center_lat"], lon=INDIA_BOUNDS["center_lon"]),
            projection_scale=4.5,  # ✅ Adjusted for full-India framing
            fitbounds="locations",  # ✅ Ensures map fits all points
        ),
        height=height,
        margin=dict(l=0, r=0, t=40, b=0),
        dragmode="pan",  # ✅ Valid value for interactive panning
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
    def add_choropleth_mapbox(col: int, coverage_col: str, title: str):
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
       "state": [
            "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
            "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand",
            "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur",
            "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab", "Rajasthan",
            "Sikkim", "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh",
            "Uttarakhand", "West Bengal", "Delhi", "Jammu and Kashmir",
            "Ladakh", "Puducherry", "Andaman and Nicobar Islands",
            "Chandigarh", "Dadra and Nagar Haveli and Daman and Diu", "Lakshadweep"
        ],
        "lat": [
            15.9, 28.2, 26.2, 25.1, 21.3,
            15.3, 22.3, 29.1, 31.8, 23.6,
            15.3, 10.3, 23.5, 19.7, 24.8,
            25.5, 23.2, 26.1, 20.3, 30.9,
            26.9, 27.3, 11.1, 17.8, 23.9,
            26.8, 30.1, 22.9, 28.6, 33.6,
            34.2, 11.9, 11.6, 30.7, 20.3, 10.6
        ],
        "lon": [
            79.7, 94.7, 92.9, 85.3, 82.0,
            74.0, 72.5, 76.8, 77.1, 85.3,
            75.7, 76.3, 78.6, 75.7, 93.9,
            91.3, 92.7, 94.3, 85.8, 75.4,
            74.2, 88.5, 78.7, 79.0, 91.6,
            80.9, 79.0, 87.8, 77.2, 75.1,
            78.0, 79.8, 92.8, 76.7, 73.0, 72.6
        ],
    }
    
    df = pd.DataFrame(states_data)
    df["selected"] = df["state"].isin(selected_states)
    
    fig = create_base_india_map(height=600, title="Click States to Select/Deselect")
    
    # Add state markers
    colors = ['orange' if selected else 'blue' for selected in df['selected']]
    
    fig.add_trace(go.Scattergeo(
        lat=df['lat'],
        lon=df['lon'],
        mode='markers+text',
        text=df['state'],
        textposition='top center',
        textfont=dict(
            family="Arial",
            size=8,          # smaller font
            color="black"    # black labels
        ),
        marker=dict(
            size=10,
            color=colors,
            symbol='circle',
            line=dict(width=2, color='black')
        ),
        name="States",
        hoverinfo= "skip"
    ))
    
    return fig