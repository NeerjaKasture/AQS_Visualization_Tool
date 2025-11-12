"""
Animation handling utilities for the AQS demo application.
Manages sensor movement animation and trajectory visualization.
"""

import numpy as np
import streamlit as st
import time
from typing import List, Dict, Tuple, Any, Optional
import plotly.graph_objects as go
from .map_creator import create_animation_frame

class AnimationController:
    """Controls animation playback and state management."""
    
    def __init__(self):
        self.is_playing = False
        self.current_step = 0
        self.total_steps = 50
        self.speed = 1.0  # Animation speed multiplier
        
    def play(self):
        """Start animation playback."""
        self.is_playing = True
        
    def pause(self):
        """Pause animation playback."""
        self.is_playing = False
        
    def stop(self):
        """Stop animation and reset to beginning."""
        self.is_playing = False
        self.current_step = 0
        
    def step_forward(self):
        """Advance animation by one step."""
        if self.current_step < self.total_steps - 1:
            self.current_step += 1
            
    def step_backward(self):
        """Move animation back by one step."""
        if self.current_step > 0:
            self.current_step -= 1
            
    def set_step(self, step: int):
        """Jump to specific animation step."""
        if 0 <= step < self.total_steps:
            self.current_step = step
            
    def set_speed(self, speed: float):
        """Set animation playback speed."""
        self.speed = max(0.1, min(5.0, speed))  # Clamp between 0.1x and 5x
        
    def get_delay(self) -> float:
        """Get delay between frames based on speed."""
        base_delay = 0.1  # 100ms base delay
        return base_delay / self.speed

@st.cache_data
def prepare_animation_data(trajectory: np.ndarray, metrics_history: List[Dict]) -> Dict[str, Any]:
    """Prepare all data needed for animation."""
    if len(trajectory) == 0 or len(metrics_history) == 0:
        return {}
    
    animation_data = {
        'trajectory': trajectory,
        'metrics': metrics_history,
        'total_steps': len(trajectory),
        'sensor_count': len(trajectory[0]) if len(trajectory) > 0 else 0
    }
    
    return animation_data

def create_animation_controls() -> Tuple[bool, bool, bool, int, float]:
    """Create animation control UI elements."""
    col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 2, 1])
    
    with col1:
        play_clicked = st.button("▶️ Play", key="play_btn")
        
    with col2:
        pause_clicked = st.button("⏸️ Pause", key="pause_btn")
        
    with col3:
        stop_clicked = st.button("⏹️ Stop", key="stop_btn")
        
    with col4:
        step = st.slider("Step", 0, 49, 0, key="step_slider")
        
    with col5:
        speed = st.select_slider(
            "Speed", 
            options=[0.5, 1.0, 1.5, 2.0, 3.0], 
            value=1.0,
            key="speed_slider"
        )
    
    return play_clicked, pause_clicked, stop_clicked, step, speed

def render_metrics_panel(metrics: Dict[str, float], step: int) -> None:
    """Render real-time metrics during animation."""
    st.subheader("📊 Real-time Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Variance Loss",
            value=f"{metrics.get('variance_loss', 0):.3f}",
            delta=f"-{0.247 - metrics.get('variance_loss', 0.247):.3f}"
        )
    
    with col2:
        st.metric(
            label="Fairness Score",
            value=f"{metrics.get('fairness', 0):.1f}",
            delta=f"+{metrics.get('fairness', 0) - 35:.1f}"
        )
    
    with col3:
        st.metric(
            label="RMSE",
            value=f"{metrics.get('rmse', 0):.2f}",
            delta=f"-{7.89 - metrics.get('rmse', 7.89):.2f}"
        )
    
    with col4:
        st.metric(
            label="Compliance %",
            value=f"{metrics.get('compliance', 0):.1f}%",
            delta=f"+{metrics.get('compliance', 0):.1f}%"
        )
    
    # Progress bar
    progress = (step + 1) / 50
    st.progress(progress, text=f"Optimization Progress: Step {step + 1}/50")

def create_sensor_trails(trajectory: np.ndarray, current_step: int, 
                        trail_length: int = 10) -> List[Tuple[np.ndarray, str]]:
    """Create fading trails behind moving sensors."""
    trails = []
    
    if len(trajectory) == 0 or current_step < 0:
        return trails
    
    # Create trail points for each sensor
    start_step = max(0, current_step - trail_length)
    
    for step in range(start_step, current_step + 1):
        if step < len(trajectory):
            # Calculate opacity based on recency
            alpha = (step - start_step + 1) / trail_length
            color = f'rgba(255, 165, 0, {alpha * 0.7})'  # Orange with fading opacity
            
            trails.append((trajectory[step], color))
    
    return trails

def animate_sensor_movement(trajectory: np.ndarray, metrics_history: List[Dict],
                           variance: np.ndarray, lat_grid: np.ndarray, lon_grid: np.ndarray,
                           show_trails: bool = True, show_variance: bool = True) -> None:
    """Main animation function with automatic playback."""
    
    if len(trajectory) == 0:
        st.error("No trajectory data available for animation")
        return
    
    # Initialize session state for animation
    if 'animation_step' not in st.session_state:
        st.session_state.animation_step = 0
    if 'animation_playing' not in st.session_state:
        st.session_state.animation_playing = False
    
    # Animation controls
    play_clicked, pause_clicked, stop_clicked, manual_step, speed = create_animation_controls()
    
    # Handle control inputs
    if play_clicked:
        st.session_state.animation_playing = True
    if pause_clicked:
        st.session_state.animation_playing = False
    if stop_clicked:
        st.session_state.animation_playing = False
        st.session_state.animation_step = 0
    
    # Manual step control overrides animation
    if manual_step != st.session_state.animation_step:
        st.session_state.animation_step = manual_step
        st.session_state.animation_playing = False
    
    # Auto-advance if playing
    if st.session_state.animation_playing:
        time.sleep(0.1 / speed)  # Speed control
        st.session_state.animation_step += 1
        
        if st.session_state.animation_step >= len(trajectory):
            st.session_state.animation_step = 0  # Loop animation
            st.session_state.animation_playing = False
        
        st.experimental_rerun()  # Refresh to show next frame
    
    current_step = st.session_state.animation_step
    current_sensors = trajectory[current_step]
    current_metrics = metrics_history[current_step] if current_step < len(metrics_history) else {}
    
    # Create and display current frame
    fig = create_animation_frame(
        current_sensors, current_step, 
        variance, lat_grid, lon_grid, 
        show_variance
    )
    
    # Add trails if requested
    if show_trails:
        trails = create_sensor_trails(trajectory, current_step)
        for trail_sensors, color in trails:
            fig.add_trace(go.Scattergeo(
                lat=trail_sensors[:, 0],
                lon=trail_sensors[:, 1],
                mode='markers',
                marker=dict(
                    size=3,
                    color=color,
                    symbol='circle'
                ),
                showlegend=False,
                hoverinfo='skip'
            ))
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Display metrics
    render_metrics_panel(current_metrics, current_step)

def create_step_by_step_viewer(trajectory: np.ndarray, metrics_history: List[Dict],
                              variance: np.ndarray, lat_grid: np.ndarray, lon_grid: np.ndarray) -> None:
    """Create step-by-step animation viewer without auto-play."""
    
    if len(trajectory) == 0:
        st.error("No trajectory data available")
        return
    
    # Step selector
    step = st.slider("Animation Step", 0, len(trajectory) - 1, 0, key="step_viewer")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Create frame
        current_sensors = trajectory[step]
        fig = create_animation_frame(
            current_sensors, step, 
            variance, lat_grid, lon_grid, 
            show_variance=True
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Metrics for current step
        if step < len(metrics_history):
            current_metrics = metrics_history[step]
            render_metrics_panel(current_metrics, step)

def export_animation_frames(trajectory: np.ndarray, variance: np.ndarray, 
                           lat_grid: np.ndarray, lon_grid: np.ndarray,
                           output_dir: str = "animation_frames") -> List[str]:
    """Export animation frames as static images."""
    import os
    from pathlib import Path
    
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    frame_files = []
    
    for step, sensors in enumerate(trajectory):
        fig = create_animation_frame(
            sensors, step, variance, lat_grid, lon_grid, show_variance=True
        )
        
        filename = output_path / f"frame_{step:03d}.png"
        fig.write_image(str(filename), width=800, height=600)
        frame_files.append(str(filename))
    
    return frame_files