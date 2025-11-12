"""
AQS Demo Application - Main Entry Point
Interactive Streamlit demo for Air Quality Sensor deployment optimization.

Run with: streamlit run demo_app.py
"""

import streamlit as st
import sys
from pathlib import Path

# Add current directory to Python path for imports
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

# Import tab modules
from tabs import render_tab1, render_tab2, render_tab3
from utils.data_loader import validate_data_files, get_data_summary

# Page configuration
st.set_page_config(
    page_title="AQS Fair Sensor Deployment Demo",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': """
        # AQS Fair Sensor Deployment Demo
        
        This demo showcases interactive approaches to fair air quality sensor deployment 
        across India, featuring:
        
        - **Sensor Placement Visualization** with animation
        - **Fairness-Aware Optimization** across multiple metrics  
        - **Budget-Constrained Allocation** with cooperative strategies
        
        Built with Streamlit, Plotly, and NumPy.
        """
    }
)

# Custom CSS for Indian flag colors and styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #FF9933 0%, #FF9933 33%, #FFFFFF 33%, #FFFFFF 66%, #138808 66%, #138808 100%);
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .main-title {
        color: #000080;
        font-size: 2.5rem;
        font-weight: bold;
        margin: 0;
    }
    
    .main-subtitle {
        color: #2E86AB;
        font-size: 1.1rem;
        margin: 0;
        font-style: italic;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #f0f2f6;
        border-radius: 5px;
        padding: 8px 16px;
        font-weight: bold;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #FF9933;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

def render_main_header():
    """Render the main application header with Indian flag colors."""
    st.markdown("""
    <div class="main-header">
        <h1 class="main-title">🇮🇳 AQS Fair Sensor Deployment Demo</h1>
        <p class="main-subtitle">Interactive Air Quality Sensor Optimization for India</p>
    </div>
    """, unsafe_allow_html=True)

def render_sidebar():
    """Render the application sidebar with navigation and info."""
    
    with st.sidebar:
        st.markdown("### 🧭 Navigation")
        st.markdown("""
        **Current Demo Features:**
        - 🌍 **Tab 1:** Sensor Placement Visualization  
        - ⚖️ **Tab 2:** Fairness Aware Placement
        - 💰 **Tab 3:** Budget Constrained Allocation
        """)
        
        st.markdown("---")
        
        # Data status
        st.markdown("### 📊 Data Status")
        data_summary = get_data_summary()
        st.text(data_summary)
        
        # Quick stats
        st.markdown("### 📈 Quick Stats")
        st.metric("K Values Available", "5", help="50, 100, 200, 1000, 4000")
        st.metric("Methods Available", "2", help="MaxVar, GDMI") 
        st.metric("Indian States", "28", help="All major states included")
        st.metric("Animation Steps", "50", help="Smooth sensor movement")
        
        st.markdown("---")
        
        # Help section
        with st.expander("❓ How to Use"):
            st.markdown("""
            **Tab 1 - Sensor Placement:**
            1. Select number of sensors (K) and method
            2. Toggle animation to see optimization process  
            3. Compare coverage across different approaches
            
            **Tab 2 - Fairness Aware:**
            1. Choose state and fairness metric
            2. Toggle overlays and sensor points
            3. Analyze performance vs fairness trade-offs
            
            **Tab 3 - Budget Allocation:**
            1. Select states from interactive map
            2. Choose budget allocation method
            3. Run optimization to see cooperative benefits
            """)
        
        # Technical info
        with st.expander("🔧 Technical Details"):
            st.markdown("""
            **Technologies Used:**
            - **Frontend:** Streamlit + Plotly
            - **Backend:** NumPy + Pandas
            - **Maps:** Plotly Geographic plots
            - **Data:** Mock datasets for demo
            
            **Performance:**
            - Cached data loading for speed
            - Optimized map rendering
            - Responsive design for mobile
            """)

def check_data_availability():
    """Check if all required data files are available."""
    validation_results = validate_data_files()
    missing_files = [f for f, exists in validation_results.items() if not exists]
    
    if missing_files:
        st.error(f"""
        ⚠️ **Missing Data Files:** {len(missing_files)} files not found
        
        Please run the data generation script first:
        ```bash
        python generate_dummy_data.py
        ```
        """)
        
        with st.expander("View Missing Files"):
            for file in missing_files[:10]:  # Show first 10
                st.write(f"❌ {file}")
            if len(missing_files) > 10:
                st.write(f"... and {len(missing_files) - 10} more files")
        
        return False
    
    return True

def main():
    """Main application entry point."""
    
    # Render header
    render_main_header()
    
    # Render sidebar
    render_sidebar()
    
    # Check data availability
    if not check_data_availability():
        st.stop()
    
    # Main content area with tabs
    st.markdown("### 📋 Select Analysis Type")
    
    tab1, tab2, tab3 = st.tabs([
        "🌍 Sensor Placement Visualization",
        "⚖️ Fairness Aware Placement", 
        "💰 Budget Constrained Allocation"
    ])
    
    # Render tab content with error handling
    with tab1:
        try:
            render_tab1()
        except Exception as e:
            st.error(f"Error in Tab 1: {str(e)}")
            st.write("Please check the data files and try again.")
    
    with tab2:
        try:
            render_tab2()
        except Exception as e:
            st.error(f"Error in Tab 2: {str(e)}")
            st.write("Please check the data files and try again.")
    
    with tab3:
        try:
            render_tab3()
        except Exception as e:
            st.error(f"Error in Tab 3: {str(e)}")
            st.write("Please check the data files and try again.")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.9rem;">
        🌟 <strong>AQS Fair Sensor Deployment Demo</strong> | 
        Built with ❤️ using Streamlit | 
        📊 <em>Demonstrating data-driven environmental policy</em>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()