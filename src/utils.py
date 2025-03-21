"""
Utility functions for the SMITE 2 CombatLog Parser.

This module provides helper functions for data parsing, conversion, and validation.
"""

import re
import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional, Tuple, Union

logger = logging.getLogger(__name__)

# Regular expression for parsing SMITE 2 timestamps
TIME_PATTERN = re.compile(r'(\d{4})\.(\d{2})\.(\d{2})-(\d{2})\.(\d{2})\.(\d{2})')


def parse_timestamp(time_str: str) -> Optional[datetime]:
    """
    Parse a SMITE 2 timestamp string into a datetime object.
    
    Args:
        time_str: A timestamp string in the format "YYYY.MM.DD-HH.MM.SS"
        
    Returns:
        A datetime object or None if parsing fails
    """
    if not time_str:
        return None
    
    try:
        # Format: YYYY.MM.DD-HH.MM.SS
        pattern = r'(\d{4})\.(\d{2})\.(\d{2})-(\d{2})\.(\d{2})\.(\d{2})'
        match = re.match(pattern, time_str)
        
        if match:
            year, month, day, hour, minute, second = map(int, match.groups())
            return datetime(year, month, day, hour, minute, second)
    except (ValueError, TypeError, AttributeError):
        pass
    
    return None


def safe_parse_numeric(value: Any, as_type: type = float) -> Optional[Union[int, float]]:
    """
    Safely parse a value as a numeric type.
    
    Args:
        value: The value to parse
        as_type: The type to convert to (int or float)
        
    Returns:
        The converted value or None if conversion fails
    """
    if value is None:
        return None
    
    if isinstance(value, (int, float)):
        return as_type(value)
    
    if not isinstance(value, str):
        return None
    
    try:
        return as_type(value)
    except (ValueError, TypeError):
        return None


def safe_load_json(json_str: str) -> Tuple[Optional[Dict[str, Any]], Optional[Exception]]:
    """
    Safely load a JSON string.
    
    Args:
        json_str: A JSON string
        
    Returns:
        A tuple of (parsed_json, exception) where exception is None if parsing succeeds
    """
    try:
        # Remove UTF-8 BOM if present
        if json_str.startswith('\ufeff'):
            json_str = json_str[1:]
        return json.loads(json_str), None
    except json.JSONDecodeError as e:
        return None, e


def clean_log_line(line: str) -> str:
    """
    Clean a log line for JSON parsing.
    
    Args:
        line: A raw log line
        
    Returns:
        A cleaned line ready for JSON parsing
    """
    # Remove UTF-8 BOM if present at the beginning of the file
    if line.startswith('\ufeff'):
        line = line[1:]
    
    # Remove whitespace
    line = line.strip()
    
    # Remove trailing comma (common in log files)
    if line.endswith(','):
        line = line[:-1]
    
    # Remove carriage returns in the middle of the line
    line = line.replace('\r', '')
    
    return line


def extract_damage_values(combat_event: Dict[str, Any]) -> Tuple[Optional[int], Optional[int]]:
    """
    Extract damage and mitigation values from a combat event.
    
    Args:
        combat_event: A combat event dictionary
        
    Returns:
        A tuple of (damage_amount, mitigated_amount)
    """
    damage = safe_parse_numeric(combat_event.get('value1'), int)
    mitigated = safe_parse_numeric(combat_event.get('value2'), int)
    return damage, mitigated


def extract_reward_values(reward_event: Dict[str, Any]) -> Tuple[Optional[int], Optional[str]]:
    """
    Extract reward amount and type from a reward event.
    
    Args:
        reward_event: A reward event dictionary
        
    Returns:
        A tuple of (amount, reward_type)
    """
    amount = safe_parse_numeric(reward_event.get('value1'), int)
    reward_type = reward_event.get('itemname', '').lower()
    return amount, reward_type 