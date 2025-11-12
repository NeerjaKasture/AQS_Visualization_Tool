# Demo Interface Build Specification

## 🎯 Goal

Build a Streamlit demo interface that shows the interactive fair sensor deployment. Can use **dummy/mock data** initially, connect to real models later.

---

## Core Features

### 1. AQ Sensor Placement Visualization

**What to Show:**

- Slider for k = [50,100,200,1000,4000]
- Choose method : MaxVar based / GDMI based
- Map showing the new sensors, old sensors, and variance based heatmap. Sensors should be marked with dots/stars
- Play visualization button that will display a animation of the sensor placement over the 50 iterations. This includes:
  - Animation of sensors moving from initial to final positions
  - Fading trails behind moving sensors
  - Metrics updating in real-time (variance loss decreasing, fairness increasing)
  - Play/Pause/Speed controls
  - Step slider
  - Live metrics

**Dummy Data Needed:**

- Current sensors: ~150 random points clustered near Delhi/Mumbai/Bangalore
- Optimized sensors: ~400 points spread across all states (can generate randomly)
- Interpolate 50 steps between initial → final
- Fake metrics per step:
  - Variance loss: 0.247 → 0.089 (linearly decreasing)

**Animation Approach:**

- Pre-compute all 50 frames
- Use plotly frames or manual frame rendering
- Slider to scrub through steps

**Libraries:**

- plotly or folium for interactive India maps

### 2. Comparison with existing methods

**What to Show:**

- 3 chloropleth district wise maps having currently placed, sarath placement and proposed placement using the k sensors selected above
- options to also show point map overlay for actual sensors

**Dummy Prototype Behavior:**

- Generate 3 different sensor distributions using the k value from Feature 1
- Choropleth maps: Use random district-level coverage values (0-100%)
- Point overlay checkbox: Toggle between district colors and actual sensor dots
- Each method shows progressively better coverage (Current < Sarath < Proposed)
- District tooltips show fake sensor counts and coverage percentages

**Libraries:**

- plotly or folium for interactive India maps
- geopandas for district boundary shape

### 3. Fairness Aware Placement

**What to Show:**

- 3 maps from left to right
- Checkbox option to enable point wise mapping of sensors ( this would work for map 1 and 3)
- Map 1: Current biased deployment (few sensors clustered in metros)
- Map 2: Fairness blind deployment (more sensors clustered in metros, but also spread to some remote/boundary regions)
- Map 2: Optimized fair deployment (sensors spread to poor/populous areas)
- Drop down to select state ( list of indian states)
- Option to choose fairness metric : population, poverty, gdp (can add more later)
- Checkbox option to add overlay ( will add overlay for population density etc)
- Metrics shown below each map for normal rmse and weighted rmse

**Dummy Data Needed:**

- State boundary shapefile: `raw_data/shapefiles/India_State_Boundary.shp` (already exists)
- Current sensors: ~150 random points clustered near Delhi/Mumbai/Bangalore
- Optimized sensors: ~400 points spread across all states (can generate randomly)
- Metrics:
  - Population covered: 85M → 210M
  - Fairness weighted RMSE: 35 → 87
  - RMSE: 7.89 → 4.12

**Dummy Prototype Behavior:**

- State dropdown: Filter all 3 maps to show only selected state boundaries
- Fairness metric dropdown: Changes overlay colors (population=red, poverty=blue, gdp=green)
- Point overlay checkbox: Shows sensor dots on maps 1 & 3 only
- Map 1 (Current): Sensors clustered in state capitals
- Map 2 (Fairness Blind): More sensors but still biased to urban areas
- Map 3 (Fair): Sensors spread to rural/poor districts based on selected metric
- Metrics below: Show fake RMSE improvements (higher → lower) and weighted RMSE
- Overlay checkbox: Add semi-transparent heatmap based on selected fairness metric

**Libraries:**

- plotly or folium for interactive India maps
- geopandas for state boundary shape

### 4. Budget constrained sensor allocation

**What to Show:**

- A interactive map of India with state boundaries - drop pin on state to select it
- 3 maps placed horizontally
- Left map shows Sarath Placement
- Centre map shows independent placement for the states selected
- Right map shows cooperative placement for the states selected
- Choose budget allocation as : Sarath's allocation, Repeat existing budget or they can upload csv file
- File uploader for CSV
- Validation: Check columns exist, state names valid
- Preview table showing allocation
- Button to "Run Optimization" (dummy: just load pre-computed results)

**CSV Format:**

```csv
state_name,required_sensors
Bihar,32
Uttar Pradesh,45
Maharashtra,18
...
```

**Dummy Prototype Behavior:**

- Interactive map: Click states to select/deselect (change color to indicate selection)
- Budget allocation dropdown:
  - "Sarath's allocation": Load predefined CSV with metro-biased allocation
  - "Repeat existing budget": Use current sensor distribution as budget
  - "Upload CSV": Enable file uploader
- CSV validation: Check for required columns, show error messages for invalid files
- Preview table: Display uploaded allocation with state names and sensor counts
- "Run Optimization" button: Show 5-second progress bar → Generate 3 different maps
- Left map (Sarath): Sensors clustered in major cities of selected states
- Center map (Independent): Each state optimized separately
- Right map (Cooperative): Cross-state optimization for better coverage
- Success message: "Optimization complete! Cooperative approach covers 23% more population."

## 🎨 UI Layout (Streamlit)

````
TAB 1: AQ Sensor Placement Visualization
├── Top Controls:
│   ├── K sensors slider (50-4000)
│   ├── Method dropdown (MaxVar/GDMI)
│   └── Play animation toggle
├── Main Map: India with sensors and variance heatmap
├── Animation Controls (when enabled):
│   ├── Play/Pause/Speed buttons
│   ├── Step slider (0-50)
│   └── Live metrics panel
└── Comparison Section: 3 choropleth maps (Current/Sarath/Proposed)

TAB 2: Fairness Aware Placement
├── Top Controls:
│   ├── State dropdown (All Indian states)
│   ├── Fairness metric dropdown (Population/Poverty/GDP)
│   ├── Show point overlay checkbox
│   └── Show fairness overlay checkbox
├── Three Maps (Left to Right):
│   ├── Current Biased Deployment
│   ├── Fairness Blind Optimization
│   └── Fairness Aware Optimization
└── Metrics Panel: RMSE and Weighted RMSE for each map

TAB 3: Budget Constrained Sensor Allocation
├── State Selection Map: Interactive India map (click to select states)
├── Budget Allocation Controls:
│   ├── Allocation method dropdown
│   ├── CSV file uploader (when "Upload CSV" selected)
│   ├── Preview table
│   └── "Run Optimization" button
└── Results: 3 horizontal maps (Sarath/Independent/Cooperative)




---------------------------------------------------------------------

## 📊 Dummy Data Generation

### Generate Fake Sensor Positions

```python
import numpy as np
import geopandas as gpd

# Load state boundaries
gdf = gpd.read_file('raw_data/shapefiles/India_State_Boundary.shp')

# Current deployment (biased to metros)
metro_centers = [
    (28.6, 77.2),  # Delhi
    (19.0, 72.8),  # Mumbai
    (12.9, 77.6),  # Bangalore
]
current_sensors = []
for center in metro_centers:
    # Cluster 50 sensors near each metro
    sensors = np.random.randn(50, 2) * 0.5 + center
    current_sensors.extend(sensors)

# Optimized deployment (spread across states)
optimized_sensors = []
for _, state in gdf.iterrows():
    # Get state bounds
    bounds = state.geometry.bounds  # (minx, miny, maxx, maxy)
    n_sensors = get_allocation(state['State_Name'])  # From CSV
    # Random points within bounds
    sensors = np.random.uniform(
        low=[bounds[1], bounds[0]],
        high=[bounds[3], bounds[2]],
        size=(n_sensors, 2)
    )
    optimized_sensors.extend(sensors)

# Save
np.save('demo_data/current_sensors.npy', current_sensors)
np.save('demo_data/optimized_sensors.npy', optimized_sensors)
````

### Generate Fake Animation Trajectory

```python
# Linear interpolation between initial and final
n_steps = 50
initial = current_sensors[:400]  # Take first 400
final = optimized_sensors

trajectory = []
for step in range(n_steps):
    alpha = step / (n_steps - 1)
    positions = (1 - alpha) * initial + alpha * final
    trajectory.append(positions)

# Save
np.save('demo_data/trajectory.npy', trajectory)
```

### Generate Fake Metrics History

```python
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

import json
with open('demo_data/metrics_history.json', 'w') as f:
    json.dump(metrics_history, f)
```

### Generate Additional Required Dummy Data

```python
import pandas as pd

# District-level coverage data for Feature 2 choropleth maps
district_data = {
    'district_name': [f'District_{i}' for i in range(1, 641)],  # ~640 districts in India
    'state_name': np.repeat(['Uttar Pradesh', 'Maharashtra', 'Bihar', 'West Bengal',
                           'Madhya Pradesh', 'Tamil Nadu', 'Rajasthan', 'Karnataka',
                           'Gujarat', 'Andhra Pradesh'] * 64, 1)[:640],
    'current_coverage': np.random.uniform(0, 40, 640),  # Low coverage
    'sarath_coverage': np.random.uniform(20, 70, 640),  # Medium coverage
    'proposed_coverage': np.random.uniform(60, 100, 640)  # High coverage
}
pd.DataFrame(district_data).to_csv('demo_data/district_coverage.csv', index=False)

# State-wise fairness metrics for Feature 3
indian_states = ['Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chhattisgarh',
                'Goa', 'Gujarat', 'Haryana', 'Himachal Pradesh', 'Jharkhand', 'Karnataka',
                'Kerala', 'Madhya Pradesh', 'Maharashtra', 'Manipur', 'Meghalaya', 'Mizoram',
                'Nagaland', 'Odisha', 'Punjab', 'Rajasthan', 'Sikkim', 'Tamil Nadu', 'Telangana',
                'Tripura', 'Uttar Pradesh', 'Uttarakhand', 'West Bengal']

fairness_data = {}
for state in indian_states:
    fairness_data[state] = {
        'population_density': np.random.uniform(50, 1200),
        'poverty_rate': np.random.uniform(8, 45),
        'gdp_per_capita': np.random.uniform(40000, 600000),
        'current_rmse': np.random.uniform(8, 15),
        'blind_rmse': np.random.uniform(5, 10),
        'fair_rmse': np.random.uniform(3, 7),
        'current_weighted_rmse': np.random.uniform(15, 35),
        'blind_weighted_rmse': np.random.uniform(10, 25),
        'fair_weighted_rmse': np.random.uniform(5, 15)
    }

with open('demo_data/fairness_metrics.json', 'w') as f:
    json.dump(fairness_data, f)

# Sample budget allocation CSVs for Feature 4
sarath_allocation = pd.DataFrame({
    'state_name': ['Maharashtra', 'Delhi', 'Karnataka', 'Gujarat', 'Tamil Nadu'],
    'required_sensors': [85, 65, 45, 40, 35]  # Metro-biased
})
sarath_allocation.to_csv('demo_data/allocation_sarath.csv', index=False)

existing_allocation = pd.DataFrame({
    'state_name': indian_states,
    'required_sensors': np.random.randint(10, 80, len(indian_states))
})
existing_allocation.to_csv('demo_data/allocation_existing.csv', index=False)

# Variance heatmap data for Feature 1
# Create a 50x50 grid covering India's geographic bounds
lat_grid = np.linspace(8, 37, 50)  # India's latitude range
lon_grid = np.linspace(68, 97, 50)  # India's longitude range
LON, LAT = np.meshgrid(lon_grid, lat_grid)

# Create Gaussian blobs centered on major cities for variance
variance_field = np.zeros((50, 50))
city_centers = [(28.6, 77.2), (19.0, 72.8), (12.9, 77.6), (22.5, 88.3), (26.9, 75.8)]  # Delhi, Mumbai, Bangalore, Kolkata, Jaipur
for lat_c, lon_c in city_centers:
    # Find closest grid points
    lat_idx = np.argmin(np.abs(lat_grid - lat_c))
    lon_idx = np.argmin(np.abs(lon_grid - lon_c))
    # Add Gaussian blob
    for i in range(50):
        for j in range(50):
            dist = np.sqrt((i - lat_idx)**2 + (j - lon_idx)**2)
            variance_field[i, j] += 0.8 * np.exp(-dist**2 / 20)

# Add some random background variance
variance_field += np.random.uniform(0.1, 0.3, (50, 50))

np.save('demo_data/variance_heatmap.npy', variance_field)
np.save('demo_data/lat_grid.npy', lat_grid)
np.save('demo_data/lon_grid.npy', lon_grid)
```

---

## 🏗️ Implementation Steps

### Step 1: Setup (30 min)

1. Create `demo_app.py`
2. Install: `pip install streamlit plotly geopandas pandas numpy folium streamlit-folium`
3. Create basic Streamlit structure with 3 tabs
4. Load state/district boundaries and verify they render
5. Set up data loading functions for all dummy datasets

### Step 2: Tab 1 - AQ Sensor Placement (3 hours)

1. Add K slider and method dropdown controls
2. Create main India map with sensors and variance heatmap
3. Implement animation toggle and controls
4. Generate trajectory data (50 steps interpolation)
5. Add comparison section with 3 choropleth maps
6. Update metrics in real-time during animation

### Step 3: Tab 2 - Fairness Aware Placement (2.5 hours)

1. Add state dropdown and fairness metric controls
2. Create 3 side-by-side maps with different deployments
3. Implement point overlay and fairness overlay toggles
4. Add metrics panel showing RMSE comparisons
5. Connect controls to update all maps dynamically

### Step 4: Tab 3 - Budget Constrained Allocation (2.5 hours)

1. Create interactive state selection map
2. Add budget allocation dropdown and CSV uploader
3. Implement CSV validation and preview table
4. Add "Run Optimization" with loading spinner
5. Display 3 result maps (Sarath/Independent/Cooperative)
6. Show success message with improvement metrics

### Step 5: Data Generation (1 hour)

1. Generate all dummy sensor positions for different K values
2. Create district coverage data for choropleth maps
3. Generate fairness metrics for all states
4. Create sample allocation CSVs
5. Add variance heatmap data

### Step 6: Polish & Testing (1 hour)

1. Add custom CSS for Indian flag color scheme
2. Add loading spinners and progress bars
3. Add tooltips and help text for all controls
4. Test all interactions and edge cases
5. Optimize performance for smooth animations

## 📁 Required Files

### Existing (Already in Repo)

- `raw_data/shapefiles/India_State_Boundary.shp` - State boundaries

### To Create (Dummy Data)

- `demo_data/current_k{K}_{method}.npy` - Current sensors for each K/method combo
- `demo_data/optimized_k{K}_{method}.npy` - Optimized sensors for each K/method combo
- `demo_data/trajectory_k{K}_{method}.npy` - 50-step animation trajectories
- `demo_data/metrics_history.json` - Animation metrics at each step
- `demo_data/district_coverage.shp` - District-level coverage for choropleth maps
- `demo_data/fairness_metrics.json` - State-wise fairness and RMSE data
- `demo_data/allocation_sarath.csv` - Sarath's allocation sample
- `demo_data/allocation_existing.csv` - Existing budget allocation sample
- `demo_data/variance_heatmap.npy` - Gaussian variance field for India

### To Create (App Code)

**Main Application:**
- `demo_app.py` - Main Streamlit application (tab navigation, page config, layout)

**Modular Tab Components:**
- `tabs/tab1_sensor_placement.py` - AQ Sensor Placement Visualization tab
- `tabs/tab2_fairness_placement.py` - Fairness Aware Placement tab  
- `tabs/tab3_budget_allocation.py` - Budget Constrained Sensor Allocation tab

**Shared Utilities:**
- `utils/data_loader.py` - Load all dummy datasets (sensors, metrics, shapefiles)
- `utils/map_creator.py` - Create India maps, choropleth, sensor overlays
- `utils/animation_handler.py` - Handle sensor animation and trajectory rendering
- `utils/csv_validator.py` - CSV upload validation and processing

**Configuration:**
- `requirements.txt` - Package dependencies
---

## ✅ Success Criteria

1. App launches without errors with 3 functional tabs
2. Tab 1: K slider and method dropdown change sensor distributions, animation plays smoothly
3. Tab 1: Choropleth comparison maps show different coverage levels
4. Tab 2: State/metric dropdowns filter maps, overlays toggle correctly
5. Tab 2: All 3 maps show distinct deployment patterns and metrics
6. Tab 3: State selection works, CSV upload validates, optimization shows results
7. All animations and loading states work smoothly
8. The code should be arranged in separate folder for each tab of the app to ensure modularity