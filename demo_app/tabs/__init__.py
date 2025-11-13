"""
Tabs package exports for demo_app.
This module exposes the render functions for each tab so they can be
imported as `from tabs import render_tab1, render_tab2, render_tab3`.
"""

from .tab1_sensor_placement import render_tab1
from .tab2_fairness_placement import render_tab2
from .tab3_budget_allocation import render_tab3

__all__ = ["render_tab1", "render_tab2", "render_tab3"]
