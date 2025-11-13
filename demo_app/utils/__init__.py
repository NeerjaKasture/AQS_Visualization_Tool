"""
Utils package for AQS demo application.
This module provides shared utilities for data loading, map creation,
animation handling, and CSV validation.
"""

from .data_loader import (
    load_sensor_positions, load_trajectory, load_metrics_history,
    load_district_coverage, load_fairness_metrics, load_allocation_csv,
    load_variance_heatmap, load_state_boundaries, get_indian_states,
    get_fairness_metrics, get_k_values, get_methods, validate_data_files,
    get_data_summary
)

from .map_creator import (
    create_base_india_map, add_sensors_to_map, add_variance_heatmap,
    create_sensor_placement_map, create_animation_frame,
    create_choropleth_comparison, create_fairness_maps,
    create_budget_allocation_maps, create_interactive_state_selection_map
)

from .animation_handler import (
    AnimationController, prepare_animation_data, create_animation_controls,
    render_metrics_panel, create_sensor_trails, animate_sensor_movement,
    create_step_by_step_viewer, export_animation_frames
)

from .csv_validator import (
    get_required_columns, get_valid_state_names, validate_csv_structure,
    validate_state_names, validate_sensor_counts, validate_business_rules,
    comprehensive_csv_validation, display_validation_results,
    clean_and_process_csv, create_sample_csv, csv_upload_interface
)

__all__ = [
    # Data loader exports
    "load_sensor_positions", "load_trajectory", "load_metrics_history",
    "load_district_coverage", "load_fairness_metrics", "load_allocation_csv",
    "load_variance_heatmap", "load_state_boundaries", "get_indian_states",
    "get_fairness_metrics", "get_k_values", "get_methods", "validate_data_files",
    "get_data_summary",
    
    # Map creator exports
    "create_base_india_map", "add_sensors_to_map", "add_variance_heatmap",
    "create_sensor_placement_map", "create_animation_frame",
    "create_choropleth_comparison", "create_fairness_maps",
    "create_budget_allocation_maps", "create_interactive_state_selection_map",
    
    # Animation handler exports
    "AnimationController", "prepare_animation_data", "create_animation_controls",
    "render_metrics_panel", "create_sensor_trails", "animate_sensor_movement",
    "create_step_by_step_viewer", "export_animation_frames",
    
    # CSV validator exports
    "get_required_columns", "get_valid_state_names", "validate_csv_structure",
    "validate_state_names", "validate_sensor_counts", "validate_business_rules",
    "comprehensive_csv_validation", "display_validation_results",
    "clean_and_process_csv", "create_sample_csv", "csv_upload_interface"
]