"""
Chart data generation module for SMITE 2 CombatLog visualizations.

This module provides functions to generate standardized chart data structures
that can be consumed by various visualization frameworks (Matplotlib, Plotly, etc.)
"""

import pandas as pd
import numpy as np
from typing import Any, Dict, List, Optional, Tuple, Union, cast

from src.utils.logging import get_logger
from src.utils.validation import safe_get_dataframe_columns, ensure_columns_exist

logger = get_logger("visualization.chart_data")


def create_kda_chart_data(df: pd.DataFrame, 
                         player_col: str = 'player_name',
                         kills_col: str = 'kills',
                         deaths_col: str = 'deaths',
                         assists_col: str = 'assists',
                         team_col: Optional[str] = 'team_id',
                         sort_by: Optional[str] = 'kda_ratio') -> Dict[str, Any]:
    """
    Create data for a KDA (Kills, Deaths, Assists) chart.
    
    Args:
        df: DataFrame containing the data
        player_col: Column name for player identifiers
        kills_col: Column name for kills
        deaths_col: Column name for deaths
        assists_col: Column name for assists
        team_col: Column name for team identification (optional)
        sort_by: Column to sort by (default is kda_ratio)
        
    Returns:
        Dictionary with chart data
    """
    # Validate required columns
    required_cols = [player_col, kills_col, deaths_col, assists_col]
    optional_cols = [team_col] if team_col else []
    
    # Check column availability
    columns_info = safe_get_dataframe_columns(df, required_cols, optional_cols)
    
    if not columns_info['all_required_available']:
        logger.warning(f"Missing required columns for KDA chart: {columns_info['missing']}")
        return {
            'error': f"Missing required columns: {columns_info['missing']}",
            'data': None,
            'valid': False
        }
    
    # Make a copy to avoid modifying the original
    plot_df = df.copy()
    
    # Calculate KDA ratio if needed for sorting
    if sort_by == 'kda_ratio' and 'kda_ratio' not in plot_df.columns:
        plot_df['kda_ratio'] = (plot_df[kills_col] + plot_df[assists_col]) / plot_df[deaths_col].replace(0, 1)
    
    # Sort if sort_by is provided and exists
    if sort_by and sort_by in plot_df.columns:
        plot_df = plot_df.sort_values(by=sort_by, ascending=False)
    
    # Create result dictionary with chart data
    result = {
        'x': plot_df[player_col].tolist(),
        'kills': plot_df[kills_col].tolist(),
        'deaths': plot_df[deaths_col].tolist(),
        'assists': plot_df[assists_col].tolist(),
        'valid': True
    }
    
    # Add KDA ratio if available
    if 'kda_ratio' in plot_df.columns:
        result['kda_ratio'] = plot_df['kda_ratio'].tolist()
    
    # Add team data if available
    if team_col and team_col in plot_df.columns:
        result['team_id'] = plot_df[team_col].tolist()
    
    return result


def create_damage_distribution_chart_data(df: pd.DataFrame,
                                        player_col: str = 'player_name',
                                        damage_types: List[str] = None,
                                        total_damage_col: str = 'total_damage',
                                        team_col: Optional[str] = 'team_id',
                                        sort_by: Optional[str] = 'total_damage') -> Dict[str, Any]:
    """
    Create data for a damage distribution chart.
    
    Args:
        df: DataFrame containing the data
        player_col: Column name for player identifiers
        damage_types: List of column names for different damage types
        total_damage_col: Column name for total damage
        team_col: Column name for team identification (optional)
        sort_by: Column to sort by
    
    Returns:
        Dictionary with chart data
    """
    # Default damage types if not provided
    damage_types = damage_types or ['physical_damage', 'magical_damage', 'true_damage']
    
    # Validate required columns
    required_cols = [player_col]
    optional_cols = damage_types + [total_damage_col, team_col] if team_col else damage_types + [total_damage_col]
    
    # Check column availability
    columns_info = safe_get_dataframe_columns(df, required_cols, optional_cols)
    
    if not columns_info['all_required_available']:
        logger.warning(f"Missing required columns for damage distribution chart: {columns_info['missing']}")
        return {
            'error': f"Missing required columns: {columns_info['missing']}",
            'data': None,
            'valid': False
        }
    
    # Make a copy to avoid modifying the original
    plot_df = df.copy()
    
    # Check which damage type columns are available
    available_damage_types = [col for col in damage_types if col in plot_df.columns]
    
    if not available_damage_types:
        logger.warning(f"No damage type columns found among: {damage_types}")
        return {
            'error': f"No damage type columns available",
            'data': None,
            'valid': False
        }
    
    # Calculate total damage if not available
    if total_damage_col not in plot_df.columns:
        plot_df[total_damage_col] = plot_df[available_damage_types].sum(axis=1)
    
    # Sort if sort_by is provided and exists
    if sort_by and sort_by in plot_df.columns:
        plot_df = plot_df.sort_values(by=sort_by, ascending=False)
    
    # Create result dictionary with chart data
    result = {
        'x': plot_df[player_col].tolist(),
        'damage_types': available_damage_types,
        'total_damage': plot_df[total_damage_col].tolist(),
        'valid': True
    }
    
    # Add each damage type
    for damage_type in available_damage_types:
        result[damage_type] = plot_df[damage_type].tolist()
    
    # Add team data if available
    if team_col and team_col in plot_df.columns:
        result['team_id'] = plot_df[team_col].tolist()
    
    return result


def create_healing_chart_data(df: pd.DataFrame,
                            player_col: str = 'player_name',
                            healing_col: str = 'healing_done',
                            self_healing_col: str = 'self_healing',
                            healing_received_col: str = 'healing_received',
                            team_col: Optional[str] = 'team_id',
                            sort_by: Optional[str] = 'healing_done') -> Dict[str, Any]:
    """
    Create data for a healing chart.
    
    Args:
        df: DataFrame containing the data
        player_col: Column name for player identifiers
        healing_col: Column name for healing done
        self_healing_col: Column name for self healing
        healing_received_col: Column name for healing received
        team_col: Column name for team identification (optional)
        sort_by: Column to sort by
    
    Returns:
        Dictionary with chart data
    """
    # Validate required columns
    required_cols = [player_col]
    optional_cols = [healing_col, self_healing_col, healing_received_col]
    if team_col:
        optional_cols.append(team_col)
    
    # Check column availability
    columns_info = safe_get_dataframe_columns(df, required_cols, optional_cols)
    
    if not columns_info['all_required_available']:
        logger.warning(f"Missing required columns for healing chart: {columns_info['missing']}")
        return {
            'error': f"Missing required columns: {columns_info['missing']}",
            'data': None,
            'valid': False
        }
    
    # Check if at least one healing column is available
    available_healing_cols = [col for col in [healing_col, self_healing_col, healing_received_col] 
                              if col in df.columns]
    
    if not available_healing_cols:
        logger.warning("No healing columns available in data")
        return {
            'error': "No healing columns available",
            'data': None,
            'valid': False
        }
    
    # Make a copy to avoid modifying the original
    plot_df = df.copy()
    
    # Sort if sort_by is provided and exists
    if sort_by and sort_by in plot_df.columns:
        plot_df = plot_df.sort_values(by=sort_by, ascending=False)
    
    # Create result dictionary with chart data
    result = {
        'x': plot_df[player_col].tolist(),
        'available_columns': available_healing_cols,
        'valid': True
    }
    
    # Add each healing metric if available
    for col in available_healing_cols:
        result[col] = plot_df[col].tolist()
    
    # Add team data if available
    if team_col and team_col in plot_df.columns:
        result['team_id'] = plot_df[team_col].tolist()
    
    return result


def create_economy_chart_data(df: pd.DataFrame,
                            player_col: str = 'player_name',
                            economy_cols: List[str] = None,
                            team_col: Optional[str] = 'team_id',
                            sort_by: Optional[str] = 'gold_earned') -> Dict[str, Any]:
    """
    Create data for an economy chart.
    
    Args:
        df: DataFrame containing the data
        player_col: Column name for player identifiers
        economy_cols: List of column names for economy metrics
        team_col: Column name for team identification (optional)
        sort_by: Column to sort by
    
    Returns:
        Dictionary with chart data
    """
    # Default economy columns if not provided
    economy_cols = economy_cols or ['gold_earned', 'gold_spent', 'gold_per_minute']
    
    # Validate required columns
    required_cols = [player_col]
    optional_cols = economy_cols
    if team_col:
        optional_cols.append(team_col)
    
    # Check column availability
    columns_info = safe_get_dataframe_columns(df, required_cols, optional_cols)
    
    if not columns_info['all_required_available']:
        logger.warning(f"Missing required columns for economy chart: {columns_info['missing']}")
        return {
            'error': f"Missing required columns: {columns_info['missing']}",
            'data': None,
            'valid': False
        }
    
    # Check if at least one economy column is available
    available_economy_cols = [col for col in economy_cols if col in df.columns]
    
    if not available_economy_cols:
        logger.warning(f"No economy columns available among: {economy_cols}")
        return {
            'error': "No economy columns available",
            'data': None,
            'valid': False
        }
    
    # Make a copy to avoid modifying the original
    plot_df = df.copy()
    
    # Sort if sort_by is provided and exists in the DataFrame
    if sort_by and sort_by in plot_df.columns:
        plot_df = plot_df.sort_values(by=sort_by, ascending=False)
    
    # Create result dictionary with chart data
    result = {
        'x': plot_df[player_col].tolist(),
        'available_columns': available_economy_cols,
        'valid': True
    }
    
    # Add each economy metric if available
    for col in available_economy_cols:
        result[col] = plot_df[col].tolist()
    
    # Add team data if available
    if team_col and team_col in plot_df.columns:
        result['team_id'] = plot_df[team_col].tolist()
    
    return result


def create_efficiency_chart_data(df: pd.DataFrame,
                               player_col: str = 'player_name',
                               efficiency_cols: List[str] = None,
                               team_col: Optional[str] = 'team_id',
                               sort_by: Optional[str] = None) -> Dict[str, Any]:
    """
    Create data for an efficiency metrics chart.
    
    Args:
        df: DataFrame containing the data
        player_col: Column name for player identifiers
        efficiency_cols: List of column names for efficiency metrics
        team_col: Column name for team identification (optional)
        sort_by: Column to sort by
    
    Returns:
        Dictionary with chart data
    """
    # Default efficiency columns if not provided
    efficiency_cols = efficiency_cols or [
        'damage_efficiency', 
        'gold_efficiency', 
        'combat_contribution', 
        'survival_efficiency'
    ]
    
    # Validate required columns
    required_cols = [player_col]
    optional_cols = efficiency_cols
    if team_col:
        optional_cols.append(team_col)
    
    # Check column availability
    columns_info = safe_get_dataframe_columns(df, required_cols, optional_cols)
    
    if not columns_info['all_required_available']:
        logger.warning(f"Missing required columns for efficiency chart: {columns_info['missing']}")
        return {
            'error': f"Missing required columns: {columns_info['missing']}",
            'data': None,
            'valid': False
        }
    
    # Check if at least one efficiency column is available
    available_efficiency_cols = [col for col in efficiency_cols if col in df.columns]
    
    if not available_efficiency_cols:
        logger.warning(f"No efficiency columns available among: {efficiency_cols}")
        return {
            'error': "No efficiency columns available",
            'data': None,
            'valid': False
        }
    
    # Make a copy to avoid modifying the original
    plot_df = df.copy()
    
    # Sort if sort_by is provided and exists
    if sort_by and sort_by in plot_df.columns:
        plot_df = plot_df.sort_values(by=sort_by, ascending=False)
    
    # Create result dictionary with chart data
    result = {
        'x': plot_df[player_col].tolist(),
        'available_columns': available_efficiency_cols,
        'valid': True
    }
    
    # Add each efficiency metric
    for col in available_efficiency_cols:
        result[col] = plot_df[col].tolist()
    
    # Add team data if available
    if team_col and team_col in plot_df.columns:
        result['team_id'] = plot_df[team_col].tolist()
    
    return result 