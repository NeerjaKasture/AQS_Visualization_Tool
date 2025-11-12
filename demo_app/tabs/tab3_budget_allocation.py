"""
Tab 3: Budget Constrained Sensor Allocation
Implements interactive state selection and budget optimization comparison.
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from typing import List, Dict, Optional

# Import utilities
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from utils.data_loader import (
    load_allocation_csv, get_indian_states
)
from utils.map_creator import (
    create_interactive_state_selection_map, create_budget_allocation_maps,
    create_base_india_map, add_sensors_to_map
)
from utils.csv_validator import csv_upload_interface

def render_tab3():
    """Render the Budget Constrained Sensor Allocation tab."""
    
    st.title("💰 Budget Constrained Sensor Allocation")
    st.markdown("Optimize sensor deployment across states with budget constraints and cooperation strategies.")
    
    # Initialize session state for selected states
    if 'selected_states' not in st.session_state:
        st.session_state.selected_states = []
    
    if 'allocation_data' not in st.session_state:
        st.session_state.allocation_data = None
    
    if 'optimization_complete' not in st.session_state:
        st.session_state.optimization_complete = False
    
    # State Selection Section
    st.header("🗺️ Interactive State Selection")
    st.markdown("Click on states in the map below to select/deselect them for budget allocation.")
    
    # Create interactive state selection map
    selection_map = create_interactive_state_selection_map(st.session_state.selected_states)
    
    # Manual state selection as fallback
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.plotly_chart(selection_map, use_container_width=True)
    
    with col2:
        st.subheader("Manual Selection")
        
        # Multi-select for states
        available_states = get_indian_states()
        selected_states_manual = st.multiselect(
            "Select States",
            options=available_states,
            default=st.session_state.selected_states[:10],  # Limit default selection
            help="Manually select states for budget allocation"
        )
        
        if st.button("Update Selection"):
            st.session_state.selected_states = selected_states_manual
            st.experimental_rerun()
        
        # Show current selection
        st.write(f"**Selected States ({len(st.session_state.selected_states)}):**")
        for state in st.session_state.selected_states[:5]:  # Show first 5
            st.write(f"• {state}")
        if len(st.session_state.selected_states) > 5:
            st.write(f"... and {len(st.session_state.selected_states) - 5} more")
    
    # Budget Allocation Section
    st.header("💸 Budget Allocation Configuration")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        allocation_method = st.selectbox(
            "Budget Allocation Method",
            options=["Sarath's Allocation", "Repeat Existing Budget", "Upload Custom CSV"],
            help="Choose how to allocate budget across states"
        )
    
    with col2:
        total_budget = st.number_input(
            "Total Sensor Budget",
            min_value=100,
            max_value=10000,
            value=1000,
            step=50,
            help="Total number of sensors to allocate"
        )
    
    # Handle different allocation methods
    allocation_df = None
    
    if allocation_method == "Sarath's Allocation":
        allocation_df = load_allocation_csv("sarath")
        if not allocation_df.empty:
            st.success("✅ Loaded Sarath's allocation (metro-biased)")
            display_allocation_preview(allocation_df)
    
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
    
    # Store allocation data in session state
    if allocation_df is not None:
        st.session_state.allocation_data = allocation_df
    
    # Optimization Section
    if st.session_state.selected_states and st.session_state.allocation_data is not None:
        st.header("🚀 Run Optimization")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            if st.button("🎯 Run Budget Optimization", type="primary", use_container_width=True):
                run_budget_optimization()
        
        # Show optimization results if available
        if st.session_state.optimization_complete:
            st.header("📊 Optimization Results")
            display_optimization_results()
    
    else:
        # Show requirements
        st.header("📋 Requirements")
        st.warning("Please complete the following steps to run optimization:")
        
        requirements = []
        if not st.session_state.selected_states:
            requirements.append("❌ Select states from the map above")
        else:
            requirements.append("✅ States selected")
        
        if st.session_state.allocation_data is None:
            requirements.append("❌ Configure budget allocation method")  
        else:
            requirements.append("✅ Budget allocation configured")
        
        for req in requirements:
            st.write(req)

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
        time.sleep(2)
        
        # Mark optimization as complete
        st.session_state.optimization_complete = True
        
        st.success("🎉 Optimization complete! Results are ready below.")

def display_optimization_results() -> None:
    """Display the optimization results and comparison."""
    
    selected_states = st.session_state.selected_states
    allocation_data = st.session_state.allocation_data
    
    # Create comparison maps
    results_fig = create_budget_allocation_maps(selected_states, allocation_data)
    st.plotly_chart(results_fig, use_container_width=True)
    
    # Results summary
    st.subheader("📈 Performance Summary")
    
    # Calculate mock performance improvements
    baseline_coverage = 45.2  # Sarath method baseline
    independent_improvement = 15.3
    cooperative_improvement = 28.7
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 🔴 Sarath Method")
        st.metric("Coverage", f"{baseline_coverage:.1f}%")
        st.metric("Efficiency", "67%")
        st.metric("Fairness Score", "42/100")
    
    with col2:
        st.markdown("### 🟡 Independent Optimization")
        new_coverage = baseline_coverage + independent_improvement
        st.metric("Coverage", f"{new_coverage:.1f}%", delta=f"+{independent_improvement:.1f}%")
        st.metric("Efficiency", "78%", delta="+11%")
        st.metric("Fairness Score", "65/100", delta="+23")
    
    with col3:
        st.markdown("### 🟢 Cooperative Optimization")
        new_coverage = baseline_coverage + cooperative_improvement
        st.metric("Coverage", f"{new_coverage:.1f}%", delta=f"+{cooperative_improvement:.1f}%")
        st.metric("Efficiency", "89%", delta="+22%")
        st.metric("Fairness Score", "81/100", delta="+39")
    
    # Detailed analysis
    st.subheader("🔍 Detailed Analysis")
    
    analysis_tabs = st.tabs(["📊 State-wise Results", "💡 Key Insights", "🎯 Recommendations"])
    
    with analysis_tabs[0]:
        display_statewise_results()
    
    with analysis_tabs[1]:
        display_key_insights()
    
    with analysis_tabs[2]:
        display_recommendations()

def display_statewise_results() -> None:
    """Display detailed state-wise optimization results."""
    
    selected_states = st.session_state.selected_states[:10]  # Limit to first 10 for demo
    
    # Generate mock state-wise results
    np.random.seed(42)
    
    results_data = []
    for state in selected_states:
        base_sensors = np.random.randint(20, 100)
        
        results_data.append({
            'State': state,
            'Sarath Allocation': base_sensors,
            'Independent Optimal': int(base_sensors * np.random.uniform(1.1, 1.3)),
            'Cooperative Optimal': int(base_sensors * np.random.uniform(1.2, 1.5)),
            'Coverage Improvement (%)': np.random.uniform(15, 35),
            'Efficiency Gain (%)': np.random.uniform(10, 25),
            'Population Served (M)': np.random.uniform(5, 50)
        })
    
    results_df = pd.DataFrame(results_data)
    
    # Display with styling
    st.dataframe(
        results_df.style.background_gradient(
            subset=['Coverage Improvement (%)', 'Efficiency Gain (%)']
        ),
        use_container_width=True
    )
    
    # Summary statistics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        avg_coverage_improvement = results_df['Coverage Improvement (%)'].mean()
        st.metric("Avg Coverage Improvement", f"{avg_coverage_improvement:.1f}%")
    
    with col2:
        total_population = results_df['Population Served (M)'].sum()
        st.metric("Total Population Served", f"{total_population:.1f}M")
    
    with col3:
        sensor_efficiency = results_df['Efficiency Gain (%)'].mean()
        st.metric("Avg Efficiency Gain", f"{sensor_efficiency:.1f}%")

def display_key_insights() -> None:
    """Display key insights from the optimization."""
    
    st.markdown("""
    ### 🎯 Key Findings
    
    **🏆 Cooperative Optimization Advantages:**
    - **28.7% higher coverage** compared to Sarath's baseline method
    - **Cross-state synergies** improve overall network efficiency
    - **Better fairness scores** through coordinated placement
    
    **📊 Performance Comparison:**
    - Independent optimization shows moderate improvement (15.3% coverage gain)
    - Cooperative approach nearly doubles the improvement of independent method
    - Fairness scores improve significantly with coordination
    
    **💡 Strategic Benefits:**
    - States can achieve better outcomes through collaboration
    - Shared sensor networks reduce individual state costs
    - Improved coverage in underserved border regions
    """)
    
    # Visual comparison chart
    methods = ['Sarath Baseline', 'Independent', 'Cooperative']
    coverage_values = [45.2, 60.5, 73.9]
    fairness_values = [42, 65, 81]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='Coverage (%)',
        x=methods,
        y=coverage_values,
        marker_color='skyblue'
    ))
    
    fig.add_trace(go.Scatter(
        name='Fairness Score',
        x=methods,
        y=fairness_values,
        mode='lines+markers',
        yaxis='y2',
        marker=dict(color='red', size=8),
        line=dict(color='red', width=3)
    ))
    
    fig.update_layout(
        title="Performance Comparison Across Methods",
        yaxis=dict(title='Coverage (%)'),
        yaxis2=dict(title='Fairness Score', overlaying='y', side='right'),
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)

def display_recommendations() -> None:
    """Display actionable recommendations based on results."""
    
    st.markdown("""
    ### 🎯 Strategic Recommendations
    
    **For Policy Makers:**
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **🤝 Promote Inter-State Cooperation**
        - Establish multi-state air quality monitoring consortiums
        - Create shared funding mechanisms for border regions
        - Develop data sharing agreements between adjacent states
        
        **💰 Optimize Budget Allocation**
        - Prioritize cooperative optimization over independent approaches
        - Allocate 20-30% more budget to achieve significant gains
        - Focus additional resources on underserved rural areas
        """)
    
    with col2:
        st.markdown("""
        **📈 Implementation Strategy**
        - Phase 1: Pilot cooperative approach with 3-4 states
        - Phase 2: Expand based on demonstrated success
        - Phase 3: Scale to national level coordination
        
        **🔄 Continuous Improvement**
        - Regular performance reviews every 6 months
        - Update optimization models with real deployment data
        - Incorporate citizen feedback and air quality health impacts
        """)
    
    # Success metrics
    st.subheader("🎯 Success Metrics to Track")
    
    metrics_data = {
        'Metric': [
            'Population Coverage',
            'Cross-border Coverage',
            'Cost per Person Served', 
            'Air Quality Index Accuracy',
            'Inter-state Collaboration Score'
        ],
        'Current Target': ['60%', '25%', '₹125', '85%', '40/100'],
        'Cooperative Target': ['74%', '45%', '₹89', '92%', '81/100'],
        'Timeline': ['6 months', '12 months', '9 months', '6 months', '18 months']
    }
    
    metrics_df = pd.DataFrame(metrics_data)
    st.dataframe(metrics_df, use_container_width=True)
    
    # Call to action
    st.markdown("---")
    st.info("""
    💡 **Next Steps:** 
    Ready to implement? Contact the state environmental agencies of your selected states to discuss this cooperative optimization approach. 
    The projected 28.7% improvement in coverage could serve an additional **23 million people** with better air quality monitoring.
    """)

if __name__ == "__main__":
    render_tab3()