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

# Page configuration
st.set_page_config(
    page_title="AQS Fair Sensor Deployment Demo",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': """
        # AQS Fair Sensor Deployment Demo
        
        This demo showcases interactive approaches to fair air quality sensor deployment 
        across India, featuring:
        
        - Sensor Placement Visualization with animation
        - Fairness-Aware Optimization across multiple metrics  
        - Budget-Constrained Allocation with cooperative strategies
        
        Built with Streamlit, Plotly, and NumPy.
        """
    }
)

# Custom CSS for Indian flag colors and styling
st.markdown("""
<style>
    /* ===== 🌞 Global Light Theme (Blue-White Professional) ===== */
    html, body, .block-container {
        background-color: #ffffff !important;
        color: #0F2B46 !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        line-height: 1.6;
    }

    /* ===== 🧭 Sidebar Hidden ===== */
    [data-testid="stSidebar"], [data-testid="stSidebarNav"] { 
        display: none !important; 
    }
    .css-1d391kg { 
        display: none !important; 
    }

    /* ===== 🏷️ Header ===== */
    .main-header {
        background: linear-gradient(90deg, #0A74DA 0%, #1268C4 50%, #0A74DA 100%);
        padding: 1.3rem 1.6rem;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 1.8rem;
        box-shadow: 0 3px 10px rgba(0,0,0,0.07);
    }
    .main-title {
        color: #ffffff;
        font-size: 2.2rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: 0.3px;
    }
    .main-subtitle {
        color: #E6F0FA;
        font-size: 1.05rem;
        margin: 4px 0 0 0;
        font-weight: 400;
    }

    /* ===== 📊 Tabs Styling ===== */
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #F4F8FD;
        border-radius: 6px;
        padding: 8px 14px;
        font-weight: 600;
        color: #0F2B46;
        border: 1px solid #D6E4F5;
        transition: all 0.2s ease;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #E6F0FA;
    }
    .stTabs [aria-selected="true"] {
        background-color: #0A74DA !important;
        color: #ffffff !important;
        border-color: #0A74DA !important;
    }

    /* ===== 📘 Text Elements ===== */
    h1, h2, h3, h4, h5, h6 {
        color: #114A8B;
        font-weight: 700;
    }
    p, li, label, span {
        color: #0F2B46 !important;
    }

    /* ===== 📈 DataFrames and Tables ===== */
    .stDataFrame, .stTable {
        background-color: #ffffff !important;
        border: 1px solid #E3EDF8 !important;
        border-radius: 8px;
        color: #0F2B46 !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.03);
    }
    .stDataFrame td, .stDataFrame th {
        color: #0F2B46 !important;
    }

    /* ===== 🎛️ Streamlit Metric, Buttons, Divider ===== */
    .stMetric label, .stMetric span { 
        color: #0F2B46 !important; 
    }
    hr { 
        border-top: 1px solid #E3EDF8; 
        margin: 1.2rem 0; 
    }

    /* ===== 🔘 Buttons ===== */
    .stButton>button {
        background-color: #0A74DA !important;
        color: white !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 0.5rem 1.1rem !important;
        font-weight: 600 !important;
        transition: background-color 0.2s ease;
    }
    .stButton>button:hover {
        background-color: #095cb0 !important;
    }

    /* ===== 📥 Download Buttons ===== */
    [data-testid="stDownloadButton"] > button {
        background-color: #E8F1FB !important;
        color: #0A74DA !important;
        border: 1px solid #BFD7F3 !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
    }
    [data-testid="stDownloadButton"] > button:hover {
        background-color: #D9E9FC !important;
    }

    /* ===== 🔽 Selectboxes / Dropdowns ===== */
    /* Closed select appearance */
    [data-baseweb="select"] > div {
        background-color: #ffffff !important;
        color: #0F2B46 !important;
        border: 1px solid #D6E4F5 !important;
        border-radius: 6px !important;
    }

    /* Dropdown popover menu */
    [data-baseweb="popover"] {
        background-color: #ffffff !important;
        color: #0F2B46 !important;
        border: 1px solid #D6E4F5 !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.08) !important;
        border-radius: 6px !important;
    }

    /* Dropdown items */
    [data-baseweb="menu-item"] {
        background-color: #ffffff !important;
        color: #0F2B46 !important;
        font-weight: 500;
        border-radius: 4px;
    }

    [data-baseweb="menu-item"]:hover {
        background-color: #E6F0FA !important;
        color: #0A74DA !important;
    }

    [aria-selected="true"][data-baseweb="menu-item"] {
        background-color: #E6F0FA !important;
        color: #0A74DA !important;
        font-weight: 600 !important;
    }
            
    /* --- Force light dropdown for new Streamlit UI --- */
    [data-testid="stSelectbox"] div[data-baseweb="select"] div {
        background-color: #ffffff !important;
        color: #0F2B46 !important;
    }

    /* The dropdown list (popover) */
    [data-testid="stSelectbox"] div[role="listbox"] {
        background-color: #ffffff !important;
        color: #0F2B46 !important;
        border: 1px solid #D6E4F5 !important;
        border-radius: 6px !important;
    }

    /* Each dropdown option */
    [data-testid="stSelectbox"] div[role="option"] {
        background-color: #ffffff !important;
        color: #0F2B46 !important;
        font-weight: 500 !important;
    }

    [data-testid="stSelectbox"] div[role="option"]:hover {
        background-color: #E6F0FA !important;
        color: #0A74DA !important;
    }

    [data-testid="stSelectbox"] div[role="option"][aria-selected="true"] {
        background-color: #E6F0FA !important;
        color: #0A74DA !important;
        font-weight: 600 !important;
    }

</style>
""", unsafe_allow_html=True)



def render_main_header():
    """Render the main application header with Indian flag colors."""
    st.markdown("""
    <div class="main-header">
        <h1 class="main-title"> AQ Sensor Deployment Demo</h1>
        <p class="main-subtitle"> Air Quality Sensor Optimization for India</p>
    </div>
    """, unsafe_allow_html=True)

def render_sidebar():
    """Deprecated: Sidebar removed for a clean, academic look."""
    return

def check_data_availability():
    """Deprecated: Data availability checks removed."""
    return True

def main():
    """Main application entry point."""
    
    # Render header
    render_main_header()
    
    # Sidebar removed; skip rendering and data availability checks
    
    # Main content area with tabs
    
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
        📊 <em>Demonstrating data-driven environmental policy</em>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()