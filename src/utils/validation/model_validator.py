"""
Model validation utilities for the SMITE 2 CombatLog Parser SDK.

This module provides utilities for validating data models to prevent attribute errors
and ensure robust data handling throughout the SDK.
"""

from typing import Any, Dict, List, Optional, Union, TypeVar, Generic, Set
import pandas as pd
import logging

T = TypeVar('T')
logger = logging.getLogger(__name__)

def safe_get_attribute(obj: Any, attr_name: str, default: T = None) -> Union[Any, T]:
    """
    Safely get an attribute from an object, returning a default value if not present.
    
    Args:
        obj: The object to get the attribute from
        attr_name: The name of the attribute to get
        default: The default value to return if the attribute does not exist
        
    Returns:
        The attribute value or the default
    """
    if obj is None:
        logger.debug(f"Attempted to access attribute '{attr_name}' on None object")
        return default
        
    if not hasattr(obj, attr_name):
        logger.debug(f"Object does not have attribute '{attr_name}', returning default")
        
    return getattr(obj, attr_name, default)

def validate_required_attributes(obj: Any, required_attrs: List[str]) -> List[str]:
    """
    Validate that an object has all the required attributes.
    
    Args:
        obj: The object to validate
        required_attrs: List of attribute names that are required
        
    Returns:
        List of missing attribute names, empty if all required attributes are present
    """
    if obj is None:
        logger.warning("Attempted to validate required attributes on None object")
        return required_attrs.copy()
        
    missing = []
    for attr in required_attrs:
        if not hasattr(obj, attr):
            missing.append(attr)
    
    if missing:
        logger.warning(f"Object is missing required attributes: {missing}")
            
    return missing

def get_model_summary(obj: Any) -> Dict[str, Any]:
    """
    Create a summary of a model object with its attributes and values.
    
    Args:
        obj: The object to summarize
        
    Returns:
        A dictionary of attribute names and values
    """
    if obj is None:
        logger.debug("Attempted to get model summary on None object")
        return {}
        
    # Get all non-callable attributes that don't start with underscore
    return {
        attr: getattr(obj, attr) 
        for attr in dir(obj) 
        if not attr.startswith('_') and not callable(getattr(obj, attr))
    }

def calculate_duration_minutes(obj: Any) -> Optional[float]:
    """
    Calculate the duration in minutes for an object that has start_time and end_time attributes.
    
    Args:
        obj: An object with start_time and end_time datetime attributes
        
    Returns:
        Duration in minutes or None if not calculable
    """
    start_time = safe_get_attribute(obj, 'start_time')
    end_time = safe_get_attribute(obj, 'end_time')
    
    if start_time and end_time:
        try:
            duration = end_time - start_time
            return duration.total_seconds() / 60
        except (TypeError, AttributeError) as e:
            logger.warning(f"Failed to calculate duration minutes: {str(e)}")
            return None
    
    logger.debug("Cannot calculate duration: missing start_time or end_time")        
    return None

def safe_get_dataframe_columns(df: Union[pd.DataFrame, List[Dict], Dict], 
                             required_cols: List[str] = None, 
                             optional_cols: List[str] = None) -> Dict[str, List[str]]:
    """
    Safely check which columns exist in a dataframe or dict-like structure.
    
    Args:
        df: Dataframe, list of dicts, or dict to check
        required_cols: List of column names that are required
        optional_cols: List of column names that are optional but useful
        
    Returns:
        Dictionary with 'available', 'missing', and 'all_required_available' keys
    """
    required_cols = required_cols or []
    optional_cols = optional_cols or []
    all_cols = required_cols + optional_cols
    
    # Handle empty or None input
    if df is None or (isinstance(df, (list, pd.DataFrame)) and len(df) == 0):
        logger.warning(f"DataFrame is empty or None, missing columns: {all_cols}")
        return {
            'available': [],
            'missing': all_cols,
            'all_required_available': False
        }
    
    # Convert to DataFrame if needed
    if not isinstance(df, pd.DataFrame):
        if isinstance(df, dict):
            # Handle single dict
            logger.debug("Converting single dict to DataFrame")
            df = pd.DataFrame([df])
        elif isinstance(df, list) and all(isinstance(item, dict) for item in df):
            # Handle list of dicts
            logger.debug("Converting list of dicts to DataFrame")
            df = pd.DataFrame(df)
        else:
            # Can't work with this type
            logger.warning(f"Cannot convert to DataFrame: unsupported type {type(df)}")
            return {
                'available': [],
                'missing': all_cols,
                'all_required_available': False
            }
    
    # Get available columns
    available_columns = [col for col in all_cols if col in df.columns]
    missing_columns = [col for col in all_cols if col not in df.columns]
    required_missing = [col for col in required_cols if col not in df.columns]
    
    if required_missing:
        logger.warning(f"DataFrame is missing required columns: {required_missing}")
    elif missing_columns:
        logger.debug(f"DataFrame is missing optional columns: {missing_columns}")
    
    return {
        'available': available_columns,
        'missing': missing_columns,
        'all_required_available': len(required_missing) == 0
    }

def ensure_columns_exist(df: pd.DataFrame, 
                         required_cols: List[str], 
                         default_values: Dict[str, Any] = None) -> pd.DataFrame:
    """
    Ensure that the required columns exist in the DataFrame, adding them with
    default values if they don't.
    
    Args:
        df: DataFrame to check and modify
        required_cols: List of column names that are required
        default_values: Dictionary mapping column names to default values
        
    Returns:
        DataFrame with all required columns
    """
    if df is None:
        logger.warning("Cannot ensure columns on None DataFrame")
        return pd.DataFrame(columns=required_cols)
    
    default_values = default_values or {}
    
    # Make a copy to avoid modifying the original
    result_df = df.copy()
    
    # Add missing columns with default values
    for col in required_cols:
        if col not in result_df.columns:
            default_value = default_values.get(col, None)
            logger.debug(f"Adding missing column '{col}' with default value: {default_value}")
            result_df[col] = default_value
            
    return result_df

def validate_dataframe_schema(df: pd.DataFrame, schema: Dict[str, type]) -> List[str]:
    """
    Validate that a DataFrame matches the expected schema.
    
    Args:
        df: DataFrame to validate
        schema: Dictionary mapping column names to expected types
        
    Returns:
        List of validation errors, empty if valid
    """
    if df is None:
        return ["DataFrame is None"]
    
    errors = []
    
    # Check for missing columns
    missing_cols = [col for col in schema.keys() if col not in df.columns]
    if missing_cols:
        errors.append(f"Missing columns: {missing_cols}")
    
    # Check column types
    for col, expected_type in schema.items():
        if col in df.columns:
            # Check if column is the expected type
            if not pd.api.types.is_dtype_equal(df[col].dtype, expected_type):
                errors.append(f"Column '{col}' has type {df[col].dtype}, expected {expected_type}")
    
    return errors 