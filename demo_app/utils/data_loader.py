"""
Data loading utilities for the AQS demo application.
Handles loading all dummy datasets and caching for performance.
"""

import numpy as np
import pandas as pd
import json
import streamlit as st
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

# Get the path to demo_data directory
DATA_DIR = Path(__file__).parent.parent / "demo_data"

@st.cache_data
def load_sensor_positions(k: int, method: str) -> Tuple[np.ndarray, np.ndarray]:
    """Load current and optimized sensor positions for given k and method."""
    current_file = DATA_DIR / f"current_k{k}_{method}.npy"
    optimized_file = DATA_DIR / f"optimized_k{k}_{method}.npy"
    
    if not current_file.exists() or not optimized_file.exists():
        st.error(f"Sensor data not found for k={k}, method={method}")
        return np.array([]), np.array([])
    
    current = np.load(current_file)
    optimized = np.load(optimized_file)
    return current, optimized

@st.cache_data
def load_trajectory(k: int, method: str) -> np.ndarray:
    """Load animation trajectory for sensor movement."""
    trajectory_file = DATA_DIR / f"trajectory_k{k}_{method}.npy"
    
    if not trajectory_file.exists():
        st.error(f"Trajectory data not found for k={k}, method={method}")
        return np.array([])
    
    return np.load(trajectory_file)

@st.cache_data
def load_metrics_history() -> List[Dict[str, float]]:
    """Load metrics history for animation."""
    metrics_file = DATA_DIR / "metrics_history.json"
    
    if not metrics_file.exists():
        st.error("Metrics history file not found")
        return []
    
    with open(metrics_file, 'r') as f:
        return json.load(f)

@st.cache_data
def load_district_coverage() -> pd.DataFrame:
    """Load district-level coverage data for choropleth maps."""
    coverage_file = DATA_DIR / "district_coverage.csv"
    
    if not coverage_file.exists():
        st.error("District coverage file not found")
        return pd.DataFrame()
    
    return pd.read_csv(coverage_file)

@st.cache_data
def load_fairness_metrics() -> Dict[str, Dict[str, float]]:
    """Load state-wise fairness and RMSE data."""
    fairness_file = DATA_DIR / "fairness_metrics.json"
    
    if not fairness_file.exists():
        st.error("Fairness metrics file not found")
        return {}
    
    with open(fairness_file, 'r') as f:
        return json.load(f)

@st.cache_data
def load_allocation_csv(allocation_type: str) -> pd.DataFrame:
    """Load budget allocation CSV."""
    filename_map = {
        "sarath": "allocation_sarath.csv",
        "existing": "allocation_existing.csv"
    }
    
    if allocation_type not in filename_map:
        st.error(f"Unknown allocation type: {allocation_type}")
        return pd.DataFrame()
    
    allocation_file = DATA_DIR / filename_map[allocation_type]
    
    if not allocation_file.exists():
        st.error(f"Allocation file not found: {filename_map[allocation_type]}")
        return pd.DataFrame()
    
    return pd.read_csv(allocation_file)

@st.cache_data
def load_variance_heatmap() -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Load variance heatmap and coordinate grids."""
    variance_file = DATA_DIR / "variance_heatmap.npy"
    lat_file = DATA_DIR / "lat_grid.npy"
    lon_file = DATA_DIR / "lon_grid.npy"
    
    missing_files = []
    if not variance_file.exists():
        missing_files.append("variance_heatmap.npy")
    if not lat_file.exists():
        missing_files.append("lat_grid.npy")
    if not lon_file.exists():
        missing_files.append("lon_grid.npy")
    
    if missing_files:
        st.error(f"Variance heatmap files not found: {missing_files}")
        return np.array([]), np.array([]), np.array([])
    
    variance = np.load(variance_file)
    lat_grid = np.load(lat_file)
    lon_grid = np.load(lon_file)
    
    return variance, lat_grid, lon_grid

@st.cache_data
def load_state_boundaries() -> Dict[str, Dict[str, float]]:
    """Load simplified state boundary data."""
    boundaries_file = DATA_DIR / "state_boundaries.json"
    
    if not boundaries_file.exists():
        st.error("State boundaries file not found")
        return {}
    
    with open(boundaries_file, 'r') as f:
        return json.load(f)

def get_indian_states() -> List[str]:
    """Get list of Indian states."""
    return [
        'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chhattisgarh',
        'Goa', 'Gujarat', 'Haryana', 'Himachal Pradesh', 'Jharkhand', 'Karnataka',
        'Kerala', 'Madhya Pradesh', 'Maharashtra', 'Manipur', 'Meghalaya', 'Mizoram',
        'Nagaland', 'Odisha', 'Punjab', 'Rajasthan', 'Sikkim', 'Tamil Nadu', 'Telangana',
        'Tripura', 'Uttar Pradesh', 'Uttarakhand', 'West Bengal'
    ]

def get_fairness_metrics() -> List[str]:
    """Get list of available fairness metrics."""
    return ['population', 'poverty', 'gdp']

def get_k_values() -> List[int]:
    """Get available K sensor values."""
    return [50, 100, 200, 1000, 4000]

def get_methods() -> List[str]:
    """Get available optimization methods."""
    return ['maxvar', 'gd']

def validate_data_files() -> Dict[str, bool]:
    """Validate that all required data files exist."""
    required_files = {
        'metrics_history.json': False,
        'district_coverage.csv': False,
        'fairness_metrics.json': False,
        'allocation_sarath.csv': False,
        'allocation_existing.csv': False,
        'variance_heatmap.npy': False,
        'lat_grid.npy': False,
        'lon_grid.npy': False,
        'state_boundaries.json': False
    }
    
    for filename in required_files:
        file_path = DATA_DIR / filename
        required_files[filename] = file_path.exists()
    
    # Check sensor position files
    k_values = get_k_values()
    methods = get_methods()
    
    for k in k_values:
        for method in methods:
            for file_type in ['current', 'optimized', 'trajectory']:
                if file_type == 'trajectory':
                    filename = f"trajectory_k{k}_{method}.npy"
                else:
                    filename = f"{file_type}_k{k}_{method}.npy"
                
                file_path = DATA_DIR / filename
                required_files[filename] = file_path.exists()
    
    return required_files

def get_data_summary() -> str:
    """Get summary of available data files."""
    validation = validate_data_files()
    total_files = len(validation)
    existing_files = sum(validation.values())
    
    summary = f"Data files: {existing_files}/{total_files} available\n"
    
    missing_files = [filename for filename, exists in validation.items() if not exists]
    if missing_files:
        summary += f"Missing files: {missing_files[:5]}"  # Show first 5 missing
        if len(missing_files) > 5:
            summary += f"... and {len(missing_files) - 5} more"
    else:
        summary += "All required data files are present ✅"
    
    return summary