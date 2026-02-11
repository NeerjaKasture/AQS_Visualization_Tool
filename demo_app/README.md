# AQS Fair Sensor Deployment Demo

## 🎯 Overview

This interactive Streamlit demo showcases fair air quality sensor deployment optimization across India. The application demonstrates three key approaches to sensor placement with real-time visualizations, animations, and performance comparisons.

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Installation

1. **Clone/Navigate to the demo directory:**
   ```bash
   cd "/path/to/aqs_app/demo_app"
   ```

2. **Install requirements:**
   ```bash
   pip install -r requirements.txt
   ```


3. **Launch the demo:**
   ```bash
   streamlit run demo_app.py
   ```

5. **Open your browser to:** http://localhost:8501

## 📊 Features

### Tab 1: Sensor Placement Visualization 🌍
- **Interactive K-sensor selection** (50 to 4,000 sensors)
- **Method comparison** (MaxVar vs GDMI algorithms)
- **Real-time animation** of sensor optimization process
- **Coverage comparison maps** across different deployment strategies
- **Performance metrics** with variance loss and RMSE tracking

### Tab 2: Fairness Aware Placement ⚖️
- **Multi-metric fairness analysis** (Population, Poverty, GDP)
- **State-level filtering** for focused analysis
- **Three deployment approaches:**
  - Current Biased (metro-clustered)
  - Fairness Blind (coverage-optimized)
  - Fairness Aware (equity-optimized)
- **Trade-off analysis** between performance and fairness
- **Detailed state comparisons** with efficiency metrics

### Tab 3: Budget Constrained Allocation 💰
- **Interactive state selection** via clickable India map
- **Multiple allocation strategies:**
  - Sarath's allocation (baseline)
  - Existing budget patterns
  - Custom CSV upload
- **Cooperative optimization** comparison
- **Budget efficiency analysis** with cross-state synergies
- **CSV validation** with comprehensive error checking

## 🗂️ Project Structure

```
demo_app/
├── demo_app.py              # Main Streamlit application
├── generate_dummy_data.py   # Data generation script
├── requirements.txt         # Python dependencies
├── README.md               # This file
├── tabs/                   # Tab implementations
│   ├── __init__.py
│   ├── tab1_sensor_placement.py
│   ├── tab2_fairness_placement.py
│   └── tab3_budget_allocation.py
├── utils/                  # Shared utilities
│   ├── __init__.py
│   ├── data_loader.py      # Data loading and caching
│   ├── map_creator.py      # Plotly map generation
│   ├── animation_handler.py # Animation controls
│   └── csv_validator.py    # CSV upload validation
└── demo_data/             # Generated dummy datasets
    ├── current_k*.npy     # Current sensor positions
    ├── optimized_k*.npy   # Optimized sensor positions
    ├── trajectory_k*.npy  # Animation trajectories
    ├── metrics_history.json
    ├── fairness_metrics.json
    ├── district_coverage.csv
    └── ...more data files
```

## 🎮 How to Use

### Getting Started
1. **Launch the app** and check the sidebar for data status
2. **Navigate between tabs** to explore different features
3. **Use the sidebar help** for detailed instructions

### Tab 1 - Sensor Placement
1. Select number of sensors (K) and optimization method
2. Toggle "Enable Animation" to see optimization process
3. Use animation controls (Play/Pause/Step) when animation is enabled
4. Compare coverage maps in the bottom section

### Tab 2 - Fairness Aware
1. Choose a state (or "All States") from dropdown
2. Select fairness metric (Population/Poverty/GDP)
3. Toggle overlays and sensor points for different views
4. Explore detailed analysis in the expandable sections

### Tab 3 - Budget Allocation
1. Select states by clicking on the map or using manual selection
2. Choose budget allocation method (or upload custom CSV)
3. Click "Run Budget Optimization" to see results
4. Review performance comparison and recommendations

## 📈 Sample Workflows

### Workflow 1: Compare Optimization Methods
1. Go to Tab 1
2. Set K=1000, Method=MaxVar, Enable Animation=True
3. Watch the optimization animation
4. Switch to Method=GDMI and compare results
5. Review coverage comparison maps at the bottom

### Workflow 2: Analyze State-Level Fairness
1. Go to Tab 2
2. Select "Maharashtra" from state dropdown
3. Choose "Population" fairness metric
4. Enable both overlays and sensor points
5. Compare RMSE metrics across all three approaches
6. Check "Detailed Analysis" tabs for insights

### Workflow 3: Budget Optimization
1. Go to Tab 3
2. Select 5-6 states from the interactive map
3. Choose "Sarath's Allocation" method
4. Run optimization and compare results
5. Review state-wise performance improvements

## 🔧 Customization

### Adding New Data
- **Sensor positions:** Add files to `demo_data/` following naming convention
- **State boundaries:** Update `generate_dummy_data.py` with real shapefiles
- **Metrics:** Modify `fairness_metrics.json` with actual performance data

### Modifying Visualizations
- **Map styles:** Edit `utils/map_creator.py` 
- **Animation speed:** Adjust in `utils/animation_handler.py`
- **Color schemes:** Update CSS in `demo_app.py`

### Adding New Features
- **New tabs:** Create files in `tabs/` directory
- **New utilities:** Add modules to `utils/` directory
- **New data sources:** Extend `utils/data_loader.py`

## 🐛 Troubleshooting

### Common Issues

**"Missing data files" error:**
```bash
# Run data generation script
python generate_dummy_data.py
```

**Import errors:**
```bash
# Reinstall requirements
pip install -r requirements.txt --force-reinstall
```

**Slow performance:**
- Reduce K value in Tab 1
- Disable animation for faster interaction
- Select fewer states in Tab 3

**CSV upload issues:**
- Check file format matches sample CSV
- Ensure all state names are valid
- Verify numeric sensor counts

### Performance Tips
- **Data caching:** App uses Streamlit caching for faster loading
- **Large datasets:** Consider reducing animation steps for K>2000
- **Memory usage:** Restart app if performance degrades over time

## 📊 Data Sources

### Dummy Data Generation
The demo uses procedurally generated data that mimics real-world patterns:
- **Sensor positions:** Gaussian distributions around major cities
- **Fairness metrics:** Randomized but realistic state-level statistics  
- **Coverage data:** Simulated district-level performance indicators
- **Animation trajectories:** Linear interpolation between positions

### Real Data Integration
To use real data:
1. Replace files in `demo_data/` with actual datasets
2. Update `utils/data_loader.py` for new data formats
3. Modify `generate_dummy_data.py` or create new data prep scripts

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create feature branch: `git checkout -b feature-name`
3. Make changes and test thoroughly
4. Submit pull request with description

### Code Style
- Follow PEP 8 Python style guidelines
- Use descriptive variable and function names
- Add docstrings to all functions
- Comment complex algorithms

### Testing
- Test all tabs with different configurations
- Verify CSV upload with various file formats
- Check animation performance with different K values
- Validate error handling with missing data

## 📝 License

This demo application is provided as-is for educational and research purposes. 
Feel free to modify and extend for your own projects.

## 📞 Support

For questions, issues, or suggestions:
1. Check this README for common solutions
2. Review code comments for implementation details
3. Open GitHub issues for bug reports
4. Contact the development team for feature requests

---

**Built with ❤️ using Streamlit | Demonstrating data-driven environmental policy**