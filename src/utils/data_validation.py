"""
Data validation utilities for the SMITE 2 CombatLog Parser SDK.

This module provides utilities for validating and sanitizing dataframes
to ensure they contain the required columns and data types for analysis.
"""

import logging
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import pandas as pd
import numpy as np

from src.utils.logging import get_logger

logger = get_logger("utils.data_validation")


def validate_dataframe(df: pd.DataFrame, 
                      required_cols: List[str], 
                      optional_cols: Optional[List[str]] = None) -> Tuple[bool, List[str]]:
    """
    Validate that a dataframe contains all required columns.
    
    Args:
        df: The dataframe to validate
        required_cols: List of column names that must be present
        optional_cols: List of optional column names that may be used if present
        
    Returns:
        Tuple of (is_valid, missing_columns)
    """
    if df is None or df.empty:
        logger.warning("Cannot validate dataframe: DataFrame is None or empty")
        return False, required_cols
    
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        logger.warning(f"DataFrame is missing required columns: {missing_cols}")
        return False, missing_cols
    
    if optional_cols:
        missing_optional = [col for col in optional_cols if col not in df.columns]
        if missing_optional:
            logger.debug(f"DataFrame is missing optional columns: {missing_optional}")
    
    return True, []


def ensure_numeric_columns(df: pd.DataFrame, 
                         numeric_cols: List[str],
                         errors: str = 'coerce') -> pd.DataFrame:
    """
    Ensure that specified columns are numeric, converting them if necessary.
    
    Args:
        df: The dataframe to process
        numeric_cols: List of column names that should be numeric
        errors: How to handle conversion errors ('ignore', 'raise', or 'coerce')
        
    Returns:
        DataFrame with numeric columns
    """
    if df is None or df.empty:
        logger.warning("Cannot ensure numeric columns: DataFrame is None or empty")
        return df
    
    result_df = df.copy()
    
    for col in numeric_cols:
        if col in result_df.columns:
            try:
                result_df[col] = pd.to_numeric(result_df[col], errors=errors)
            except Exception as e:
                logger.error(f"Error converting column '{col}' to numeric: {str(e)}")
                if errors == 'raise':
                    raise
        else:
            logger.debug(f"Column '{col}' not found, skipping numeric conversion")
    
    return result_df


def fill_missing_values(df: pd.DataFrame, 
                      fill_values: Dict[str, Any]) -> pd.DataFrame:
    """
    Fill missing values in specified columns with provided values.
    
    Args:
        df: The dataframe to process
        fill_values: Dictionary mapping column names to fill values
        
    Returns:
        DataFrame with filled values
    """
    if df is None or df.empty:
        logger.warning("Cannot fill missing values: DataFrame is None or empty")
        return df
    
    result_df = df.copy()
    
    for col, fill_value in fill_values.items():
        if col in result_df.columns:
            result_df[col] = result_df[col].fillna(fill_value)
        else:
            logger.debug(f"Column '{col}' not found, skipping fill")
    
    return result_df


def add_missing_columns(df: pd.DataFrame, 
                      column_defaults: Dict[str, Any]) -> pd.DataFrame:
    """
    Add missing columns to a dataframe with default values.
    
    Args:
        df: The dataframe to process
        column_defaults: Dictionary mapping column names to default values
        
    Returns:
        DataFrame with added columns
    """
    if df is None:
        logger.warning("Cannot add missing columns: DataFrame is None")
        return pd.DataFrame(columns=list(column_defaults.keys()))
    
    result_df = df.copy()
    
    for col, default_value in column_defaults.items():
        if col not in result_df.columns:
            result_df[col] = default_value
    
    return result_df


def filter_dataframe(df: pd.DataFrame,
                    filters: Dict[str, Any],
                    numeric_threshold_filters: Optional[Dict[str, Tuple[str, float]]] = None) -> pd.DataFrame:
    """
    Filter a dataframe based on column values and thresholds.
    
    Args:
        df: The dataframe to filter
        filters: Dictionary mapping column names to values for equality filtering
        numeric_threshold_filters: Dictionary mapping column names to tuples of (operator, threshold)
                                  where operator is one of '>', '<', '>=', '<=', '=='
        
    Returns:
        Filtered DataFrame
    """
    if df is None or df.empty:
        logger.warning("Cannot filter dataframe: DataFrame is None or empty")
        return df
    
    result_df = df.copy()
    
    # Apply equality filters
    for col, value in filters.items():
        if col in result_df.columns:
            result_df = result_df[result_df[col] == value]
        else:
            logger.warning(f"Column '{col}' not found, skipping filter")
    
    # Apply numeric threshold filters
    if numeric_threshold_filters:
        for col, (operator, threshold) in numeric_threshold_filters.items():
            if col in result_df.columns:
                try:
                    if operator == '>':
                        result_df = result_df[result_df[col] > threshold]
                    elif operator == '<':
                        result_df = result_df[result_df[col] < threshold]
                    elif operator == '>=':
                        result_df = result_df[result_df[col] >= threshold]
                    elif operator == '<=':
                        result_df = result_df[result_df[col] <= threshold]
                    elif operator == '==':
                        result_df = result_df[result_df[col] == threshold]
                    else:
                        logger.warning(f"Unknown operator '{operator}', skipping filter")
                except Exception as e:
                    logger.error(f"Error applying threshold filter to column '{col}': {str(e)}")
            else:
                logger.warning(f"Column '{col}' not found, skipping threshold filter")
    
    return result_df


def safe_divide(numerator: Union[float, pd.Series], 
               denominator: Union[float, pd.Series], 
               default: float = 0.0) -> Union[float, pd.Series]:
    """
    Safely divide, returning a default value when the denominator is zero.
    
    Args:
        numerator: The numerator for division
        denominator: The denominator for division
        default: The default value to return when denominator is zero
        
    Returns:
        Result of division or default value
    """
    if isinstance(numerator, pd.Series) and isinstance(denominator, pd.Series):
        # If both are Series, use pandas' built-in vectorized operations
        result = pd.Series(default, index=numerator.index)
        # Find where denominator is zero or NaN
        zero_mask = (denominator == 0) | denominator.isna()
        # For non-zero denominators, do the division
        result.loc[~zero_mask] = numerator.loc[~zero_mask] / denominator.loc[~zero_mask]
        return result
    elif isinstance(numerator, pd.Series):
        # If only numerator is a Series
        if denominator == 0 or pd.isna(denominator):
            return pd.Series(default, index=numerator.index)
        return numerator / denominator
    elif isinstance(denominator, pd.Series):
        # If only denominator is a Series
        result = pd.Series(default, index=denominator.index)
        # Find where denominator is zero or NaN
        zero_mask = (denominator == 0) | denominator.isna()
        # For non-zero denominators, do the division
        result.loc[~zero_mask] = numerator / denominator.loc[~zero_mask]
        return result
    else:
        # For scalar values, simple if-else
        return numerator / denominator if denominator != 0 else default


def sort_dataframe(df: pd.DataFrame, 
                 sort_by: str, 
                 ascending: bool = False) -> pd.DataFrame:
    """
    Sort a dataframe by a column, handling the case where the column doesn't exist.
    
    Args:
        df: The dataframe to sort
        sort_by: The column to sort by
        ascending: Whether to sort in ascending order
        
    Returns:
        Sorted DataFrame or original if the column doesn't exist
    """
    if df is None or df.empty:
        logger.warning("Cannot sort dataframe: DataFrame is None or empty")
        return df
    
    if sort_by in df.columns:
        # Sort a copy to avoid modifying the original
        return df.sort_values(by=sort_by, ascending=ascending).copy()
    else:
        logger.warning(f"Cannot sort by '{sort_by}': column not found")
        return df.copy()


def normalize_values(df: pd.DataFrame, 
                   columns: List[str], 
                   method: str = 'min_max') -> pd.DataFrame:
    """
    Normalize values in specified columns.
    
    Args:
        df: The dataframe to process
        columns: List of column names to normalize
        method: Normalization method ('min_max', 'z_score')
        
    Returns:
        DataFrame with normalized columns
    """
    if df is None or df.empty:
        logger.warning("Cannot normalize values: DataFrame is None or empty")
        return df
    
    result_df = df.copy()
    
    for col in columns:
        if col in result_df.columns:
            try:
                values = result_df[col]
                if method == 'min_max':
                    min_val = values.min()
                    max_val = values.max()
                    if max_val > min_val:
                        result_df[f'{col}_normalized'] = (values - min_val) / (max_val - min_val)
                    else:
                        result_df[f'{col}_normalized'] = 0.5  # Default for constant columns
                elif method == 'z_score':
                    mean = values.mean()
                    std = values.std()
                    if std > 0:
                        result_df[f'{col}_normalized'] = (values - mean) / std
                    else:
                        result_df[f'{col}_normalized'] = 0.0  # Default for constant columns
                else:
                    logger.warning(f"Unknown normalization method '{method}'")
            except Exception as e:
                logger.error(f"Error normalizing column '{col}': {str(e)}")
        else:
            logger.warning(f"Column '{col}' not found, skipping normalization")
    
    return result_df


def round_numeric_columns(df: pd.DataFrame, 
                        columns: List[str], 
                        decimals: int = 2) -> pd.DataFrame:
    """
    Round numeric columns to specified number of decimal places.
    
    Args:
        df: The dataframe to process
        columns: List of column names to round
        decimals: Number of decimal places
        
    Returns:
        DataFrame with rounded columns
    """
    if df is None or df.empty:
        logger.warning("Cannot round columns: DataFrame is None or empty")
        return df
    
    result_df = df.copy()
    
    for col in columns:
        if col in result_df.columns:
            try:
                result_df[col] = result_df[col].round(decimals)
            except Exception as e:
                logger.warning(f"Error rounding column '{col}': {str(e)}")
        else:
            logger.debug(f"Column '{col}' not found, skipping rounding")
    
    return result_df


def dataframe_to_records(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Convert a DataFrame to a list of dictionaries (records).
    Handles None or empty DataFrames gracefully.
    
    Args:
        df: The DataFrame to convert
        
    Returns:
        List of dictionaries representing each row
    """
    if df is None or df.empty:
        return []
    
    try:
        # Convert DataFrame to records
        records = df.to_dict(orient='records')
        
        # Handle NaN values by converting them to None
        for record in records:
            for key, value in record.items():
                if pd.isna(value):
                    record[key] = None
        
        return records
    except Exception as e:
        logger.error(f"Error converting DataFrame to records: {str(e)}")
        return []


def records_to_dataframe(records: List[Dict[str, Any]], 
                        default_columns: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Convert a list of dictionaries (records) to a DataFrame.
    Handles None or empty lists gracefully.
    
    Args:
        records: List of dictionaries to convert
        default_columns: Optional list of columns that should be present in the result
        
    Returns:
        DataFrame created from the records
    """
    if not records:
        if default_columns:
            return pd.DataFrame(columns=default_columns)
        return pd.DataFrame()
    
    try:
        # Convert records to DataFrame
        df = pd.DataFrame(records)
        
        # Add any missing default columns
        if default_columns:
            for col in default_columns:
                if col not in df.columns:
                    df[col] = None
        
        return df
    except Exception as e:
        logger.error(f"Error converting records to DataFrame: {str(e)}")
        if default_columns:
            return pd.DataFrame(columns=default_columns)
        return pd.DataFrame()


def ensure_output_format(data: Union[pd.DataFrame, List[Dict[str, Any]], None], 
                        format_type: str = 'dataframe',
                        default_columns: Optional[List[str]] = None) -> Union[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Ensure the data is in the requested format (DataFrame or list of dictionaries).
    
    Args:
        data: The data to convert (DataFrame, list of dicts, or None)
        format_type: The desired format ('dataframe' or 'records')
        default_columns: Optional list of columns that should be present in the result
        
    Returns:
        Data in the requested format
    """
    # Handle None case
    if data is None:
        if format_type.lower() == 'dataframe':
            return pd.DataFrame(columns=default_columns if default_columns else [])
        else:  # records format
            return []
    
    # Convert to the requested format
    if format_type.lower() == 'dataframe':
        if isinstance(data, pd.DataFrame):
            # Already a DataFrame, just add missing columns if needed
            if default_columns:
                return add_missing_columns(data, {col: None for col in default_columns})
            return data
        else:
            # Assume it's a list of dicts or similar
            return records_to_dataframe(data, default_columns)
    else:  # records format
        if isinstance(data, pd.DataFrame):
            return dataframe_to_records(data)
        else:
            # Already a list of dicts, return as is
            return data


class ColumnMapper:
    """
    Utility for mapping and standardizing column names in DataFrames.
    
    This class provides utilities for ensuring consistent column naming
    throughout the analysis pipeline, making it more robust against
    changes in the underlying data structure.
    """
    
    # Standard column name mappings
    STANDARD_MAPPINGS = {
        # Entity type mappings
        'source_type': 'source_entity_type',
        'target_type': 'target_entity_type',
        
        # Damage mappings
        'damage_amount': 'raw_damage',
        'mitigated_amount': 'mitigated_damage',
        
        # Economy mappings
        'gold_earned': 'total_gold',
        'experience_earned': 'total_xp',
        
        # Other common mappings
        'player_id': 'player_key',
        'team_id': 'team_number',
    }
    
    @classmethod
    def standardize_columns(cls, df: pd.DataFrame, mappings: Optional[Dict[str, str]] = None) -> pd.DataFrame:
        """
        Standardize column names in a DataFrame using mappings.
        
        This method will:
        1. Add mapped columns if original column exists but mapped doesn't
        2. Not override existing columns if both original and mapped exist
        3. Apply custom mappings if provided
        
        Args:
            df: DataFrame to standardize
            mappings: Optional custom mappings to use instead of standard
            
        Returns:
            DataFrame with standardized column names
        """
        if df is None or df.empty:
            return df
            
        result_df = df.copy()
        mappings = mappings or cls.STANDARD_MAPPINGS
        
        # For each mapping, add the standardized column if needed
        for original, mapped in mappings.items():
            if original in result_df.columns and mapped not in result_df.columns:
                result_df[mapped] = result_df[original]
                logger.debug(f"Mapped column '{original}' to '{mapped}'")
                
        return result_df
    
    @classmethod
    def ensure_columns(cls, df: pd.DataFrame, required_columns: List[str], 
                     default_value: Any = 0) -> pd.DataFrame:
        """
        Ensure specified columns exist in the DataFrame.
        
        Args:
            df: DataFrame to check
            required_columns: List of columns that must exist
            default_value: Default value for missing columns
            
        Returns:
            DataFrame with required columns added if missing
        """
        if df is None:
            logger.warning("Received None DataFrame, creating empty DataFrame with required columns")
            return pd.DataFrame(columns=required_columns)
            
        if df.empty:
            # If DataFrame is empty, ensure it has the required columns
            result_df = df.copy()
            for col in required_columns:
                if col not in result_df.columns:
                    result_df[col] = pd.Series(dtype=float)  # Create empty series with proper type
            return result_df
            
        result_df = df.copy()
        
        # Add any missing required columns
        for col in required_columns:
            if col not in result_df.columns:
                result_df[col] = default_value
                logger.debug(f"Added missing required column '{col}' with default value {default_value}")
                
        return result_df
    
    @classmethod
    def map_and_ensure(cls, df: pd.DataFrame, required_columns: List[str], 
                     mappings: Optional[Dict[str, str]] = None,
                     default_value: Any = 0) -> pd.DataFrame:
        """
        Combine standardize_columns and ensure_columns in one operation.
        
        Args:
            df: DataFrame to process
            required_columns: List of columns that must exist
            mappings: Optional custom mappings to use
            default_value: Default value for missing columns
            
        Returns:
            DataFrame with standardized and required columns
        """
        # First standardize the columns
        result_df = cls.standardize_columns(df, mappings)
        
        # Then ensure required columns exist
        result_df = cls.ensure_columns(result_df, required_columns, default_value)
        
        return result_df 