#!/usr/bin/env python3
"""
Generate all dummy data required for the AQS demo application.
Run this script once to create all necessary data files.
"""

import numpy as np
import pandas as pd
import json
import os
from pathlib import Path

# Ensure demo_data directory exists
demo_data_dir = Path(__file__).parent / "demo_data"
demo_data_dir.mkdir(exist_ok=True)

print("Generating dummy data for AQS demo...")

# Indian states list
INDIAN_STATES = [
    'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chhattisgarh',
    'Goa', 'Gujarat', 'Haryana', 'Himachal Pradesh', 'Jharkhand', 'Karnataka',
    'Kerala', 'Madhya Pradesh', 'Maharashtra', 'Manipur', 'Meghalaya', 'Mizoram',
    'Nagaland', 'Odisha', 'Punjab', 'Rajasthan', 'Sikkim', 'Tamil Nadu', 'Telangana',
    'Tripura', 'Uttar Pradesh', 'Uttarakhand', 'West Bengal'
]

# Major city centers (lat, lon)
METRO_CENTERS = [
    (28.6, 77.2),  # Delhi
    (19.0, 72.8),  # Mumbai
    (12.9, 77.6),  # Bangalore
    (22.5, 88.3),  # Kolkata
    (26.9, 75.8),  # Jaipur
]

def generate_sensor_positions():
    """Generate sensor positions for different K values and methods"""
    print("Generating sensor positions...")
    
    K_VALUES = [50, 100, 200, 1000, 4000]
    METHODS = ['MaxVar', 'GDMI']
    
    for k in K_VALUES:
        for method in METHODS:
            # Current sensors (biased to metros)
            current_sensors = []
            sensors_per_metro = k // len(METRO_CENTERS)
            
            for i, (lat_c, lon_c) in enumerate(METRO_CENTERS):
                n_sensors = sensors_per_metro + (k % len(METRO_CENTERS) if i == 0 else 0)
                # Add Gaussian noise around metro centers
                sensors = np.random.randn(n_sensors, 2) * 0.3 + np.array([lat_c, lon_c])
                current_sensors.extend(sensors)
            
            current_sensors = np.array(current_sensors[:k])
            
            # Optimized sensors (spread across India)
            # India bounding box: lat 8-37, lon 68-97
            optimized_sensors = []
            for _ in range(k):
                lat = np.random.uniform(8, 37)
                lon = np.random.uniform(68, 97)
                optimized_sensors.append([lat, lon])
            
            optimized_sensors = np.array(optimized_sensors)
            
            # Save sensor positions
            np.save(demo_data_dir / f"current_k{k}_{method}.npy", current_sensors)
            np.save(demo_data_dir / f"optimized_k{k}_{method}.npy", optimized_sensors)
            
            # Generate animation trajectory (50 steps)
            trajectory = []
            n_steps = 50
            for step in range(n_steps):
                alpha = step / (n_steps - 1)
                positions = (1 - alpha) * current_sensors + alpha * optimized_sensors
                trajectory.append(positions)
            
            np.save(demo_data_dir / f"trajectory_k{k}_{method}.npy", trajectory)

def generate_metrics_history():
    """Generate metrics history for animation"""
    print("Generating metrics history...")
    
    metrics_history = []
    for step in range(50):
        alpha = step / 49
        metrics_history.append({
            'step': step,
            'variance_loss': 0.247 - alpha * (0.247 - 0.089),
            'fairness': 35 + alpha * (87 - 35),
            'rmse': 7.89 - alpha * (7.89 - 4.12),
            'compliance': alpha * 100
        })
    
    with open(demo_data_dir / 'metrics_history.json', 'w') as f:
        json.dump(metrics_history, f, indent=2)

def generate_district_coverage():
    """Generate district-level coverage data for choropleth maps"""
    print("Generating district coverage data...")
    
    # Generate ~640 districts across states
    districts_per_state = {
        'Uttar Pradesh': 75, 'Maharashtra': 36, 'Bihar': 38, 'West Bengal': 23,
        'Madhya Pradesh': 52, 'Tamil Nadu': 38, 'Rajasthan': 33, 'Karnataka': 31,
        'Gujarat': 33, 'Andhra Pradesh': 26, 'Odisha': 30, 'Telangana': 33,
        'Kerala': 14, 'Jharkhand': 24, 'Assam': 34, 'Punjab': 23,
        'Chhattisgarh': 28, 'Haryana': 22, 'Jammu and Kashmir': 22,
        'Uttarakhand': 13, 'Himachal Pradesh': 12, 'Tripura': 8,
        'Meghalaya': 11, 'Manipur': 16, 'Nagaland': 12, 'Goa': 2,
        'Arunachal Pradesh': 25, 'Mizoram': 11, 'Sikkim': 6
    }
    
    district_data = []
    district_id = 1
    
    for state, num_districts in districts_per_state.items():
        for i in range(num_districts):
            district_data.append({
                'district_id': district_id,
                'district_name': f'{state}_District_{i+1}',
                'state_name': state,
                'current_coverage': np.random.uniform(0, 40),  # Low coverage
                'sarath_coverage': np.random.uniform(20, 70),  # Medium coverage
                'proposed_coverage': np.random.uniform(60, 100),  # High coverage
                'current_sensors': np.random.randint(0, 5),
                'sarath_sensors': np.random.randint(2, 8),
                'proposed_sensors': np.random.randint(5, 12)
            })
            district_id += 1
    
    pd.DataFrame(district_data).to_csv(demo_data_dir / 'district_coverage.csv', index=False)

def generate_fairness_metrics():
    """Generate state-wise fairness and RMSE data"""
    print("Generating fairness metrics...")
    
    fairness_data = {}
    for state in INDIAN_STATES:
        fairness_data[state] = {
            'population_density': float(np.random.uniform(50, 1200)),
            'poverty_rate': float(np.random.uniform(8, 45)),
            'gdp_per_capita': float(np.random.uniform(40000, 600000)),
            'current_rmse': float(np.random.uniform(8, 15)),
            'blind_rmse': float(np.random.uniform(5, 10)),
            'fair_rmse': float(np.random.uniform(3, 7)),
            'current_weighted_rmse': float(np.random.uniform(15, 35)),
            'blind_weighted_rmse': float(np.random.uniform(10, 25)),
            'fair_weighted_rmse': float(np.random.uniform(5, 15)),
            'population_covered': int(np.random.uniform(100000, 50000000)),
            'fairness_score': float(np.random.uniform(0.3, 0.95))
        }
    
    with open(demo_data_dir / 'fairness_metrics.json', 'w') as f:
        json.dump(fairness_data, f, indent=2)

def generate_allocation_csvs():
    """Generate sample budget allocation CSVs"""
    print("Generating allocation CSVs...")
    
    # Sarath's allocation (metro-biased)
    sarath_allocation = pd.DataFrame({
        'state_name': ['Maharashtra', 'Delhi', 'Karnataka', 'Gujarat', 'Tamil Nadu',
                      'Uttar Pradesh', 'West Bengal', 'Rajasthan', 'Madhya Pradesh'],
        'required_sensors': [85, 65, 45, 40, 35, 30, 28, 25, 22]
    })
    sarath_allocation.to_csv(demo_data_dir / 'allocation_sarath.csv', index=False)
    
    # Existing allocation
    existing_allocation = pd.DataFrame({
        'state_name': INDIAN_STATES,
        'required_sensors': np.random.randint(10, 80, len(INDIAN_STATES))
    })
    existing_allocation.to_csv(demo_data_dir / 'allocation_existing.csv', index=False)

def generate_variance_heatmap():
    """Generate variance heatmap data for India"""
    print("Generating variance heatmap...")
    
    # Create 50x50 grid covering India
    lat_grid = np.linspace(8, 37, 50)  # India's latitude range
    lon_grid = np.linspace(68, 97, 50)  # India's longitude range
    
    # Create variance field with Gaussian blobs around major cities
    variance_field = np.zeros((50, 50))
    
    for lat_c, lon_c in METRO_CENTERS:
        # Find closest grid points
        lat_idx = np.argmin(np.abs(lat_grid - lat_c))
        lon_idx = np.argmin(np.abs(lon_grid - lon_c))
        
        # Add Gaussian blob
        for i in range(50):
            for j in range(50):
                dist = np.sqrt((i - lat_idx)**2 + (j - lon_idx)**2)
                variance_field[i, j] += 0.8 * np.exp(-dist**2 / 20)
    
    # Add random background variance
    variance_field += np.random.uniform(0.1, 0.3, (50, 50))
    
    # Normalize to 0-1 range
    variance_field = (variance_field - variance_field.min()) / (variance_field.max() - variance_field.min())
    
    np.save(demo_data_dir / 'variance_heatmap.npy', variance_field)
    np.save(demo_data_dir / 'lat_grid.npy', lat_grid)
    np.save(demo_data_dir / 'lon_grid.npy', lon_grid)

def generate_state_boundaries_simple():
    """Generate simplified state boundary data"""
    print("Generating simplified state boundaries...")
    
    # Simple rectangular boundaries for each state (for demo purposes)
    state_bounds = {}
    
    # Divide India roughly into state regions
    lat_min, lat_max = 8, 37
    lon_min, lon_max = 68, 97
    
    rows, cols = 6, 5  # Rough grid
    lat_step = (lat_max - lat_min) / rows
    lon_step = (lon_max - lon_min) / cols
    
    for i, state in enumerate(INDIAN_STATES[:30]):  # Use first 30 states
        row = i // cols
        col = i % cols
        
        state_bounds[state] = {
            'min_lat': lat_min + row * lat_step,
            'max_lat': lat_min + (row + 1) * lat_step,
            'min_lon': lon_min + col * lon_step,
            'max_lon': lon_min + (col + 1) * lon_step
        }
    
    with open(demo_data_dir / 'state_boundaries.json', 'w') as f:
        json.dump(state_bounds, f, indent=2)

if __name__ == "__main__":
    # Generate all dummy data
    generate_sensor_positions()
    generate_metrics_history()
    generate_district_coverage()
    generate_fairness_metrics()
    generate_allocation_csvs()
    generate_variance_heatmap()
    generate_state_boundaries_simple()
    
    print(f"\nDummy data generation complete!")
    print(f"Files created in: {demo_data_dir}")
    print(f"Total files: {len(list(demo_data_dir.glob('*')))}")