"""
Data models for the SMITE 2 CombatLog Parser.

This module defines the data structures used to represent the parsed CombatLog data.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Set


@dataclass
class Match:
    """Represents a SMITE 2 match."""
    
    match_id: str
    log_mode: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Player:
    """Represents a player in a SMITE 2 match."""
    
    player_id: int
    player_name: str
    god_id: Optional[str] = None
    god_name: Optional[str] = None
    role: Optional[str] = None
    team_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Event:
    """Represents an event in the CombatLog."""
    
    event_id: int
    event_type: str
    event_subtype: str
    raw_time: str
    event_timestamp: datetime
    source_owner: Optional[str] = None
    target_owner: Optional[str] = None
    location_x: Optional[float] = None
    location_y: Optional[float] = None
    item_id: Optional[str] = None
    item_name: Optional[str] = None
    value1: Optional[Union[str, int, float]] = None
    value2: Optional[Union[str, int, float]] = None
    text: Optional[str] = None
    raw_data: Dict[str, Any] = field(default_factory=dict)
    
    # References to other entities
    source_player_id: Optional[int] = None
    target_player_id: Optional[int] = None
    match_id: Optional[str] = None


@dataclass
class CombatEvent(Event):
    """Specialized class for combat events."""
    
    damage_amount: Optional[int] = None
    mitigated_amount: Optional[int] = None
    is_critical: bool = False
    ability_id: Optional[str] = None
    ability_name: Optional[str] = None
    source_god: Optional[str] = None
    target_god: Optional[str] = None


@dataclass
class EconomyEvent(Event):
    """Specialized class for economy events."""
    
    reward_type: Optional[str] = None
    amount: Optional[int] = None
    source_type: Optional[str] = None


@dataclass
class ItemEvent(Event):
    """Specialized class for item purchase events."""
    
    purchase_location: Optional[str] = None
    

@dataclass
class PlayerEvent(Event):
    """Specialized class for player-related events."""
    
    god_id: Optional[str] = None
    god_name: Optional[str] = None
    role: Optional[str] = None 