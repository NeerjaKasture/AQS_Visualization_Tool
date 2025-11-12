"""
CSV validation utilities for the AQS demo application.
Handles upload, validation, and processing of budget allocation CSV files.
"""

import pandas as pd
import streamlit as st
import io
from typing import Dict, List, Tuple, Optional, Set

def get_required_columns() -> List[str]:
    """Get list of required columns for allocation CSV."""
    return ['state_name', 'required_sensors']

def get_valid_state_names() -> Set[str]:
    """Get set of valid Indian state names."""
    return {
        'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chhattisgarh',
        'Goa', 'Gujarat', 'Haryana', 'Himachal Pradesh', 'Jharkhand', 'Karnataka',
        'Kerala', 'Madhya Pradesh', 'Maharashtra', 'Manipur', 'Meghalaya', 'Mizoram',
        'Nagaland', 'Odisha', 'Punjab', 'Rajasthan', 'Sikkim', 'Tamil Nadu', 'Telangana',
        'Tripura', 'Uttar Pradesh', 'Uttarakhand', 'West Bengal',
        # Also include some common variations/abbreviations
        'Delhi', 'NCT of Delhi', 'Jammu and Kashmir', 'Ladakh'
    }

def validate_csv_structure(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """Validate basic CSV structure and columns."""
    errors = []
    
    # Check if DataFrame is empty
    if df.empty:
        errors.append("CSV file is empty")
        return False, errors
    
    # Check required columns
    required_cols = get_required_columns()
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        errors.append(f"Missing required columns: {missing_cols}")
    
    # Check for extra unexpected columns
    expected_cols = set(required_cols)
    actual_cols = set(df.columns)
    extra_cols = actual_cols - expected_cols
    
    if extra_cols:
        errors.append(f"Unexpected columns found: {list(extra_cols)}")
    
    return len(errors) == 0, errors

def validate_state_names(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """Validate state names in the CSV."""
    errors = []
    valid_states = get_valid_state_names()
    
    if 'state_name' not in df.columns:
        errors.append("Missing 'state_name' column")
        return False, errors
    
    # Check for missing/null state names
    null_states = df['state_name'].isnull().sum()
    if null_states > 0:
        errors.append(f"{null_states} rows have missing state names")
    
    # Check for invalid state names
    invalid_states = []
    for state in df['state_name'].dropna().unique():
        if state not in valid_states:
            invalid_states.append(state)
    
    if invalid_states:
        errors.append(f"Invalid state names found: {invalid_states}")
        errors.append(f"Valid states: {sorted(valid_states)}")
    
    # Check for duplicate states
    duplicates = df['state_name'].value_counts()
    duplicate_states = duplicates[duplicates > 1].index.tolist()
    
    if duplicate_states:
        errors.append(f"Duplicate states found: {duplicate_states}")
    
    return len(errors) == 0, errors

def validate_sensor_counts(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """Validate sensor count values."""
    errors = []
    
    if 'required_sensors' not in df.columns:
        errors.append("Missing 'required_sensors' column")
        return False, errors
    
    # Check for missing/null sensor counts
    null_sensors = df['required_sensors'].isnull().sum()
    if null_sensors > 0:
        errors.append(f"{null_sensors} rows have missing sensor counts")
    
    # Check data type - should be numeric
    try:
        sensor_counts = pd.to_numeric(df['required_sensors'], errors='coerce')
        non_numeric = sensor_counts.isnull().sum() - null_sensors
        
        if non_numeric > 0:
            errors.append(f"{non_numeric} rows have non-numeric sensor counts")
    except Exception as e:
        errors.append(f"Error converting sensor counts to numeric: {str(e)}")
        return False, errors
    
    # Check for valid ranges
    valid_sensors = sensor_counts.dropna()
    
    # Check for negative values
    negative_count = (valid_sensors < 0).sum()
    if negative_count > 0:
        errors.append(f"{negative_count} rows have negative sensor counts")
    
    # Check for unreasonably high values (> 10000)
    high_count = (valid_sensors > 10000).sum()
    if high_count > 0:
        errors.append(f"{high_count} rows have unreasonably high sensor counts (>10,000)")
    
    # Check for zero values (warning, not error)
    zero_count = (valid_sensors == 0).sum()
    if zero_count > 0:
        errors.append(f"Warning: {zero_count} states have zero sensors allocated")
    
    return len([e for e in errors if not e.startswith("Warning")]) == 0, errors

def validate_business_rules(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """Validate business-specific rules."""
    errors = []
    
    # Check total sensor allocation is reasonable
    if 'required_sensors' in df.columns:
        try:
            total_sensors = pd.to_numeric(df['required_sensors'], errors='coerce').sum()
            
            if total_sensors < 50:
                errors.append(f"Total sensors ({total_sensors}) seems too low (minimum recommended: 50)")
            elif total_sensors > 50000:
                errors.append(f"Total sensors ({total_sensors}) seems too high (maximum recommended: 50,000)")
            
            # Check distribution - no single state should have >50% of all sensors
            max_allocation = pd.to_numeric(df['required_sensors'], errors='coerce').max()
            if max_allocation > total_sensors * 0.5:
                max_state = df.loc[df['required_sensors'].idxmax(), 'state_name']
                errors.append(f"State '{max_state}' has {max_allocation} sensors ({max_allocation/total_sensors*100:.1f}% of total) - consider more balanced distribution")
        
        except Exception as e:
            errors.append(f"Error in business rule validation: {str(e)}")
    
    return len(errors) == 0, errors

def comprehensive_csv_validation(df: pd.DataFrame) -> Tuple[bool, Dict[str, List[str]]]:
    """Run all validation checks and return comprehensive results."""
    validation_results = {
        'structure': [],
        'state_names': [],
        'sensor_counts': [],
        'business_rules': []
    }
    
    # Run all validation checks
    structure_valid, structure_errors = validate_csv_structure(df)
    validation_results['structure'] = structure_errors
    
    if structure_valid:  # Only check other aspects if structure is valid
        state_valid, state_errors = validate_state_names(df)
        validation_results['state_names'] = state_errors
        
        sensor_valid, sensor_errors = validate_sensor_counts(df)
        validation_results['sensor_counts'] = sensor_errors
        
        business_valid, business_errors = validate_business_rules(df)
        validation_results['business_rules'] = business_errors
        
        overall_valid = state_valid and sensor_valid and business_valid
    else:
        overall_valid = False
    
    return overall_valid, validation_results

def display_validation_results(validation_results: Dict[str, List[str]], 
                              is_valid: bool) -> None:
    """Display validation results in Streamlit UI."""
    
    if is_valid:
        st.success("✅ CSV validation passed! File is ready for processing.")
    else:
        st.error("❌ CSV validation failed. Please fix the following issues:")
    
    # Display specific error categories
    for category, errors in validation_results.items():
        if errors:
            category_name = category.replace('_', ' ').title()
            
            with st.expander(f"{category_name} Issues ({len(errors)})"):
                for error in errors:
                    if error.startswith("Warning"):
                        st.warning(error)
                    else:
                        st.error(error)

def clean_and_process_csv(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and process validated CSV data."""
    processed_df = df.copy()
    
    # Clean state names (strip whitespace, standardize case)
    if 'state_name' in processed_df.columns:
        processed_df['state_name'] = processed_df['state_name'].str.strip()
    
    # Convert sensor counts to integers
    if 'required_sensors' in processed_df.columns:
        processed_df['required_sensors'] = pd.to_numeric(
            processed_df['required_sensors'], 
            errors='coerce'
        ).astype('Int64')  # Nullable integer type
    
    # Remove rows with null values
    processed_df = processed_df.dropna()
    
    # Sort by state name for consistency
    processed_df = processed_df.sort_values('state_name').reset_index(drop=True)
    
    return processed_df

def create_sample_csv() -> pd.DataFrame:
    """Create a sample CSV for user reference."""
    sample_data = {
        'state_name': [
            'Maharashtra', 'Uttar Pradesh', 'Karnataka', 'Gujarat', 'Tamil Nadu',
            'Rajasthan', 'West Bengal', 'Madhya Pradesh', 'Bihar', 'Andhra Pradesh'
        ],
        'required_sensors': [85, 75, 45, 40, 35, 30, 28, 25, 22, 20]
    }
    
    return pd.DataFrame(sample_data)

def csv_upload_interface() -> Optional[pd.DataFrame]:
    """Create CSV upload interface with validation."""
    
    st.subheader("📁 Upload Budget Allocation CSV")
    
    # Show format requirements
    with st.expander("📋 CSV Format Requirements"):
        st.write("Your CSV file must contain the following columns:")
        st.code("""
state_name,required_sensors
Maharashtra,85
Karnataka,45
Gujarat,40
...""")
        
        # Download sample CSV
        sample_df = create_sample_csv()
        csv_sample = sample_df.to_csv(index=False)
        
        st.download_button(
            label="📥 Download Sample CSV",
            data=csv_sample,
            file_name="sample_allocation.csv",
            mime="text/csv"
        )
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Choose CSV file",
        type=['csv'],
        help="Upload a CSV file with state names and required sensor counts"
    )
    
    if uploaded_file is not None:
        try:
            # Read CSV
            df = pd.read_csv(uploaded_file)
            
            # Show raw data preview
            st.subheader("📊 Data Preview")
            st.dataframe(df.head(10), use_container_width=True)
            st.caption(f"Showing first 10 rows of {len(df)} total rows")
            
            # Validate CSV
            is_valid, validation_results = comprehensive_csv_validation(df)
            
            # Display validation results
            display_validation_results(validation_results, is_valid)
            
            if is_valid:
                # Clean and process data
                processed_df = clean_and_process_csv(df)
                
                # Show processed data summary
                st.subheader("📈 Processed Data Summary")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total States", len(processed_df))
                
                with col2:
                    total_sensors = processed_df['required_sensors'].sum()
                    st.metric("Total Sensors", f"{total_sensors:,}")
                
                with col3:
                    avg_sensors = processed_df['required_sensors'].mean()
                    st.metric("Avg per State", f"{avg_sensors:.1f}")
                
                # Show final processed data
                st.dataframe(processed_df, use_container_width=True)
                
                return processed_df
            
        except Exception as e:
            st.error(f"Error reading CSV file: {str(e)}")
            st.info("Please ensure your file is a valid CSV format.")
    
    return None