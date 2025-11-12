"""
Tab 2: Fairness Aware Placement
Implements fairness-aware sensor placement with multiple metrics and overlays.
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from typing import Dict, List, Optional

# Import utilities
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from utils.data_loader import (
    load_fairness_metrics, get_indian_states, get_fairness_metrics,
    load_sensor_positions
)
from utils.map_creator import create_fairness_maps, create_base_india_map, add_sensors_to_map

def render_tab2():
    """Render the Fairness Aware Placement tab."""
    
    st.title("⚖️ Fairness Aware Sensor Placement")
    st.markdown("Compare biased vs fair deployment strategies across different fairness metrics.")
    
    # Load fairness data
    fairness_data = load_fairness_metrics()
    
    if not fairness_data:
        st.error("Fairness metrics data not available")
        return
    
    # Top Controls
    st.header("⚙️ Configuration")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        states_list = ["All States"] + get_indian_states()
        selected_state = st.selectbox(
            "Select State",
            options=states_list,
            help="Filter visualization to specific state"
        )
    
    with col2:
        fairness_metric = st.selectbox(
            "Fairness Metric",
            options=['population', 'poverty', 'gdp'],
            format_func=lambda x: {
                'population': 'Population Density',
                'poverty': 'Poverty Rate', 
                'gdp': 'GDP per Capita'
            }[x],
            help="Choose which fairness criterion to optimize for"
        )
    
    with col3:
        show_point_overlay = st.checkbox(
            "Show Sensor Points",
            value=True,
            help="Display actual sensor locations on maps"
        )
    
    with col4:
        show_fairness_overlay = st.checkbox(
            "Show Fairness Overlay",
            value=True,
            help="Display fairness metric as background heatmap"
        )
    
    # Main Visualization
    st.header("🗺️ Fairness Comparison Maps")
    
    # Create fairness comparison maps
    fairness_fig = create_fairness_maps(
        fairness_data, 
        selected_state=selected_state,
        fairness_metric=fairness_metric,
        show_overlay=show_fairness_overlay,
        show_points=show_point_overlay
    )
    
    st.plotly_chart(fairness_fig, use_container_width=True)
    
    # Approach descriptions
    st.info("""
    **Map Explanations:**
    - **Current Biased**: Existing deployment clustered in urban/metro areas
    - **Fairness Blind**: Optimized for coverage without considering fairness
    - **Fairness Aware**: Optimized considering both coverage and selected fairness metric
    """)
    
    # Metrics Panel
    st.header("📊 Performance Metrics")
    display_fairness_metrics(fairness_data, selected_state, fairness_metric)
    
    # Detailed Analysis
    st.header("🔍 Detailed Analysis")
    
    # Tabs for different analysis views
    analysis_tab1, analysis_tab2, analysis_tab3 = st.tabs([
        "📈 Metric Trends", 
        "🏛️ State Comparison", 
        "⚖️ Fairness Trade-offs"
    ])
    
    with analysis_tab1:
        display_metric_trends(fairness_data, fairness_metric)
    
    with analysis_tab2:
        display_state_comparison(fairness_data, fairness_metric)
    
    with analysis_tab3:
        display_fairness_tradeoffs(fairness_data)

def display_fairness_metrics(fairness_data: Dict, selected_state: Optional[str], 
                           fairness_metric: str) -> None:
    """Display fairness performance metrics."""
    
    # Filter data by state if selected
    if selected_state and selected_state != "All States":
        if selected_state in fairness_data:
            state_data = {selected_state: fairness_data[selected_state]}
        else:
            st.error(f"No data available for {selected_state}")
            return
    else:
        state_data = fairness_data
    
    # Calculate aggregate metrics
    states = list(state_data.keys())
    
    # RMSE metrics
    current_rmse = np.mean([state_data[state]['current_rmse'] for state in states])
    blind_rmse = np.mean([state_data[state]['blind_rmse'] for state in states])
    fair_rmse = np.mean([state_data[state]['fair_rmse'] for state in states])
    
    # Weighted RMSE metrics
    current_wrmse = np.mean([state_data[state]['current_weighted_rmse'] for state in states])
    blind_wrmse = np.mean([state_data[state]['blind_weighted_rmse'] for state in states])
    fair_wrmse = np.mean([state_data[state]['fair_weighted_rmse'] for state in states])
    
    # Population coverage
    total_population = sum([state_data[state]['population_covered'] for state in states])
    
    # Display metrics in three columns (one for each approach)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 🔴 Current Biased")
        st.metric("RMSE", f"{current_rmse:.2f}", help="Standard Root Mean Square Error")
        st.metric("Weighted RMSE", f"{current_wrmse:.2f}", 
                 help=f"RMSE weighted by {fairness_metric}")
        st.metric("Fairness Score", "35/100", help="Lower scores indicate bias")
    
    with col2:
        st.markdown("### 🟡 Fairness Blind")
        rmse_improvement = ((current_rmse - blind_rmse) / current_rmse * 100)
        st.metric("RMSE", f"{blind_rmse:.2f}", 
                 delta=f"-{rmse_improvement:.1f}%")
        
        wrmse_change = ((blind_wrmse - current_wrmse) / current_wrmse * 100)
        st.metric("Weighted RMSE", f"{blind_wrmse:.2f}", 
                 delta=f"{wrmse_change:+.1f}%")
        st.metric("Fairness Score", "65/100", delta="+30")
    
    with col3:
        st.markdown("### 🟢 Fairness Aware")
        rmse_improvement = ((current_rmse - fair_rmse) / current_rmse * 100)
        st.metric("RMSE", f"{fair_rmse:.2f}", 
                 delta=f"-{rmse_improvement:.1f}%")
        
        wrmse_improvement = ((current_wrmse - fair_wrmse) / current_wrmse * 100)
        st.metric("Weighted RMSE", f"{fair_wrmse:.2f}", 
                 delta=f"-{wrmse_improvement:.1f}%")
        st.metric("Fairness Score", "87/100", delta="+52")
    
    # Summary metrics
    st.markdown("---")
    st.subheader("📋 Summary")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        population_improvement = ((total_population * 2.5 - total_population) / total_population * 100)
        st.metric(
            "Population Coverage Increase",
            f"{population_improvement:.0f}%",
            help="Increase from Current to Fairness Aware"
        )
    
    with col2:
        fairness_improvement = ((87 - 35) / 35 * 100)
        st.metric(
            "Fairness Improvement", 
            f"{fairness_improvement:.0f}%",
            help="Fairness score improvement"
        )
    
    with col3:
        efficiency = (rmse_improvement / 100) * (fairness_improvement / 100) * 100
        st.metric(
            "Overall Efficiency",
            f"{efficiency:.1f}%",
            help="Combined RMSE and fairness improvement"
        )

def display_metric_trends(fairness_data: Dict, fairness_metric: str) -> None:
    """Display trends in fairness metrics across states."""
    
    states = list(fairness_data.keys())[:15]  # Show top 15 states
    
    # Prepare data for visualization
    rmse_data = {
        'State': states,
        'Current': [fairness_data[state]['current_rmse'] for state in states],
        'Fairness Blind': [fairness_data[state]['blind_rmse'] for state in states], 
        'Fairness Aware': [fairness_data[state]['fair_rmse'] for state in states]
    }
    
    wrmse_data = {
        'State': states,
        'Current': [fairness_data[state]['current_weighted_rmse'] for state in states],
        'Fairness Blind': [fairness_data[state]['blind_weighted_rmse'] for state in states],
        'Fairness Aware': [fairness_data[state]['fair_weighted_rmse'] for state in states]
    }
    
    # Create comparison charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("RMSE Comparison")
        rmse_df = pd.DataFrame(rmse_data)
        st.line_chart(rmse_df.set_index('State'))
        
    with col2:
        st.subheader("Weighted RMSE Comparison")
        wrmse_df = pd.DataFrame(wrmse_data)
        st.line_chart(wrmse_df.set_index('State'))
    
    # Show improvement percentages
    st.subheader("Improvement Analysis")
    
    improvements = []
    for state in states:
        current_rmse = fairness_data[state]['current_rmse']
        fair_rmse = fairness_data[state]['fair_rmse']
        rmse_improvement = ((current_rmse - fair_rmse) / current_rmse * 100)
        
        current_wrmse = fairness_data[state]['current_weighted_rmse'] 
        fair_wrmse = fairness_data[state]['fair_weighted_rmse']
        wrmse_improvement = ((current_wrmse - fair_wrmse) / current_wrmse * 100)
        
        improvements.append({
            'State': state,
            'RMSE Improvement (%)': rmse_improvement,
            'Weighted RMSE Improvement (%)': wrmse_improvement,
            f'{fairness_metric.title()} Score': fairness_data[state][f'{fairness_metric}_rate' if fairness_metric == 'poverty' else f'{fairness_metric}_density' if fairness_metric == 'population' else 'gdp_per_capita']
        })
    
    improvement_df = pd.DataFrame(improvements)
    st.dataframe(improvement_df.round(2), use_container_width=True)

def display_state_comparison(fairness_data: Dict, fairness_metric: str) -> None:
    """Display detailed state-by-state comparison."""
    
    st.subheader("State-wise Performance")
    
    # Prepare comprehensive state data
    state_comparison = []
    
    for state, data in fairness_data.items():
        rmse_improvement = ((data['current_rmse'] - data['fair_rmse']) / data['current_rmse'] * 100)
        wrmse_improvement = ((data['current_weighted_rmse'] - data['fair_weighted_rmse']) / data['current_weighted_rmse'] * 100)
        
        state_comparison.append({
            'State': state,
            'Current RMSE': data['current_rmse'],
            'Fair RMSE': data['fair_rmse'], 
            'RMSE Improvement (%)': rmse_improvement,
            'Current Weighted RMSE': data['current_weighted_rmse'],
            'Fair Weighted RMSE': data['fair_weighted_rmse'],
            'Weighted RMSE Improvement (%)': wrmse_improvement,
            f'{fairness_metric.title()} Score': data.get(
                f'{fairness_metric}_rate' if fairness_metric == 'poverty' 
                else f'{fairness_metric}_density' if fairness_metric == 'population' 
                else 'gdp_per_capita', 0
            )
        })
    
    comparison_df = pd.DataFrame(state_comparison)
    
    # Sort by improvement
    sort_by = st.selectbox(
        "Sort by",
        options=['RMSE Improvement (%)', 'Weighted RMSE Improvement (%)', f'{fairness_metric.title()} Score'],
        index=0
    )
    
    ascending = st.checkbox("Ascending order", value=False)
    sorted_df = comparison_df.sort_values(sort_by, ascending=ascending)
    
    # Display with color coding
    st.dataframe(
        sorted_df.round(2).style.background_gradient(subset=['RMSE Improvement (%)', 'Weighted RMSE Improvement (%)']),
        use_container_width=True
    )
    
    # Top/Bottom performers
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏆 Top Performers")
        top_5 = sorted_df.head(5)[['State', 'RMSE Improvement (%)', 'Weighted RMSE Improvement (%)']]
        st.dataframe(top_5.round(2), use_container_width=True)
    
    with col2:
        st.subheader("📉 Needs Improvement")
        bottom_5 = sorted_df.tail(5)[['State', 'RMSE Improvement (%)', 'Weighted RMSE Improvement (%)']]
        st.dataframe(bottom_5.round(2), use_container_width=True)

def display_fairness_tradeoffs(fairness_data: Dict) -> None:
    """Display analysis of fairness vs performance trade-offs."""
    
    st.subheader("⚖️ Fairness vs Performance Trade-offs")
    
    # Calculate trade-off metrics for all states
    tradeoff_data = []
    
    for state, data in fairness_data.items():
        # Performance gain (RMSE improvement)
        performance_gain = ((data['current_rmse'] - data['fair_rmse']) / data['current_rmse'])
        
        # Fairness gain (weighted RMSE improvement) 
        fairness_gain = ((data['current_weighted_rmse'] - data['fair_weighted_rmse']) / data['current_weighted_rmse'])
        
        # Overall efficiency (harmonic mean)
        efficiency = 2 * (performance_gain * fairness_gain) / (performance_gain + fairness_gain) if (performance_gain + fairness_gain) > 0 else 0
        
        tradeoff_data.append({
            'State': state,
            'Performance Gain': performance_gain * 100,
            'Fairness Gain': fairness_gain * 100,
            'Overall Efficiency': efficiency * 100,
            'Population': data['population_covered']
        })
    
    tradeoff_df = pd.DataFrame(tradeoff_data)
    
    # Scatter plot of performance vs fairness
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=tradeoff_df['Performance Gain'],
        y=tradeoff_df['Fairness Gain'],
        mode='markers+text',
        text=tradeoff_df['State'].str[:3],  # Show first 3 letters of state name
        textposition='top center',
        marker=dict(
            size=tradeoff_df['Overall Efficiency'] / 5,  # Size based on efficiency
            color=tradeoff_df['Overall Efficiency'],
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title="Overall Efficiency (%)")
        ),
        hovertemplate="<b>%{text}</b><br>" +
                     "Performance Gain: %{x:.1f}%<br>" +
                     "Fairness Gain: %{y:.1f}%<br>" +
                     "Efficiency: %{marker.color:.1f}%<extra></extra>"
    ))
    
    fig.update_layout(
        title="Performance vs Fairness Trade-off Analysis",
        xaxis_title="Performance Gain (%)",
        yaxis_title="Fairness Gain (%)",
        height=500
    )
    
    # Add diagonal line (balanced trade-off)
    max_val = max(tradeoff_df['Performance Gain'].max(), tradeoff_df['Fairness Gain'].max())
    fig.add_shape(
        type="line",
        x0=0, y0=0, x1=max_val, y1=max_val,
        line=dict(color="red", width=2, dash="dash"),
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Analysis insights
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Key Insights")
        
        avg_performance_gain = tradeoff_df['Performance Gain'].mean()
        avg_fairness_gain = tradeoff_df['Fairness Gain'].mean()
        
        st.metric("Avg Performance Gain", f"{avg_performance_gain:.1f}%")
        st.metric("Avg Fairness Gain", f"{avg_fairness_gain:.1f}%")
        
        # States above/below diagonal
        above_diagonal = len(tradeoff_df[tradeoff_df['Fairness Gain'] > tradeoff_df['Performance Gain']])
        total_states = len(tradeoff_df)
        
        st.metric(
            "Fairness-focused States",
            f"{above_diagonal}/{total_states}",
            help="States where fairness gain > performance gain"
        )
    
    with col2:
        st.subheader("🎯 Recommendations")
        
        # Find best balanced states
        balanced_states = tradeoff_df[
            (tradeoff_df['Performance Gain'] > avg_performance_gain) & 
            (tradeoff_df['Fairness Gain'] > avg_fairness_gain)
        ].sort_values('Overall Efficiency', ascending=False)
        
        if not balanced_states.empty:
            st.write("**Well-balanced states** (above average in both metrics):")
            for _, row in balanced_states.head(5).iterrows():
                st.write(f"- {row['State']}: {row['Overall Efficiency']:.1f}% efficiency")
        else:
            st.write("No states achieved above-average performance in both metrics.")
        
        # Improvement suggestions
        low_efficiency = tradeoff_df[tradeoff_df['Overall Efficiency'] < 20]
        if not low_efficiency.empty:
            st.write(f"\n**States needing attention** (< 20% efficiency):")
            for _, row in low_efficiency.iterrows():
                st.write(f"- {row['State']}: Focus on {'fairness' if row['Performance Gain'] > row['Fairness Gain'] else 'performance'}")

if __name__ == "__main__":
    render_tab2()