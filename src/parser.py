"""
Main parser module for SMITE 2 CombatLog data.

This module provides the CombatLogParser class which handles the parsing and transformation
of SMITE 2 CombatLog data into a structured format for analysis.
"""

import json
import logging
import os
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, Set, Generator, Union

from .models import Match, Player, Event, CombatEvent, EconomyEvent, ItemEvent, PlayerEvent
from .utils import (
    parse_timestamp, 
    safe_parse_numeric, 
    safe_load_json, 
    clean_log_line,
    extract_damage_values,
    extract_reward_values
)

logger = logging.getLogger(__name__)


class CombatLogParser:
    """
    Parser for SMITE 2 CombatLog data.
    
    This class handles the parsing and transformation of raw CombatLog data into
    a structured format suitable for analysis.
    """
    
    # Classification mappings for SMITE 2 entities
    OBJECTIVES = {
        'Order Titan', 'Chaos Titan', 
        'Order Tower', 'Chaos Tower',
        'Order Phoenix', 'Chaos Phoenix', 
        'Gold Fury', 'Pyromancer', 'Minotaur'
    }

    JUNGLE_CAMPS = {
        'Harpy', 'Elder Harpy', 'Roaming Harpy',
        'Chimera', 'Alpha Chimera',
        'Manticore', 'Alpha Manticore',
        'Centaur', 'Alpha Centaur',
        'Scorpion', 'Alpha Scorpion',
        'Satyr', 'Elder Satyr',
        'Cyclops Warrior', 'Rogue Cyclops',
        'Queen Naga', 'Naga Soldier'
    }

    MINIONS = {
        'Archer', 'Champion Archer', 'Fire Archer',
        'Brute', 'Fire Brute',
        'Swordsman', 'Fire Swordsman'
    }
    
    def __init__(self, log_file: str = None, debug: bool = False):
        """
        Initialize the parser.
        
        Args:
            log_file: Path to the log file to parse
            debug: Whether to enable debug logging
        """
        self.log_file = log_file
        self.debug = debug
        self._setup_logging()
        
        # Data structures
        self.match: Optional[Match] = None
        self.players: Dict[str, Player] = {}  # player_name -> Player
        self.player_id_counter = 1
        self.events: List[Event] = []
        self.event_id_counter = 1
        
        # Specialized event collections
        self.combat_events: List[CombatEvent] = []
        self.economy_events: List[EconomyEvent] = []
        self.item_events: List[ItemEvent] = []
        self.player_events: List[PlayerEvent] = []
        
        # Raw data for reference
        self.raw_events: List[Dict[str, Any]] = []
    
    def _setup_logging(self):
        """Configure logging based on debug setting."""
        level = logging.DEBUG if self.debug else logging.INFO
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('combat_log_parser.log')
            ]
        )
    
    def parse(self, log_file: Optional[str] = None) -> bool:
        """
        Parse the log file and populate the data structures.
        
        Args:
            log_file: Optional path to the log file (overrides the one set in __init__)
            
        Returns:
            True if parsing was successful, False otherwise
        """
        try:
            if log_file:
                self.log_file = log_file
                
            if not self.log_file or not os.path.exists(self.log_file):
                logger.error(f"Log file not found: {self.log_file}")
                return False
            
            logger.info(f"Parsing log file: {self.log_file}")
            
            # Clear any previous data
            self.raw_events = []
            self.events = []
            self.players = {}
            self.match = None
            
            # Parse the raw events
            self._parse_raw_events()
            
            # Check if we got any events
            if not self.raw_events:
                logger.error("No valid events were parsed from the log file.")
                return False
            
            # Extract match metadata
            self._extract_match_metadata()
            
            # Extract player information
            self._extract_player_info()
            
            # Process events
            self._process_events()
            
            logger.info(f"Parsing complete. {len(self.events)} events processed.")
            return True
        except Exception as e:
            logger.exception(f"Error parsing log file: {e}")
            return False
    
    def _parse_raw_events(self) -> None:
        """Parse the raw events from the log file."""
        line_count = 0
        error_count = 0
        
        with open(self.log_file, 'r', encoding='utf-8-sig') as f:
            for line in f:
                line_count += 1
                
                # Clean the line
                line = clean_log_line(line)
                if not line:
                    continue
                
                # Parse the JSON
                event_data, error = safe_load_json(line)
                if error:
                    error_count += 1
                    logger.error(f"Error parsing line {line_count}: {error}")
                    if error_count < 10:  # Limit logging
                        logger.error(f"Problematic line: {line[:100]}...")
                    continue
                
                # Store the raw event
                self.raw_events.append(event_data)
        
        logger.info(f"Parsed {line_count} lines with {error_count} errors. {len(self.raw_events)} valid events found.")
    
    def _extract_match_metadata(self) -> None:
        """Extract match metadata from the start event."""
        start_events = [e for e in self.raw_events if e.get('eventType') == 'start']
        if not start_events:
            logger.warning("No start event found in the log file.")
            self.match = Match(match_id="unknown", log_mode="unknown")
            return
        
        # Use the first start event
        start_event = start_events[0]
        match_id = start_event.get('matchID', 'unknown')
        log_mode = start_event.get('logMode', 'unknown')
        
        self.match = Match(match_id=match_id, log_mode=log_mode)
        logger.info(f"Match metadata extracted: ID={match_id}, Mode={log_mode}")
        
        # Find match start and end times
        events_with_time = [e for e in self.raw_events if 'time' in e]
        if events_with_time:
            first_time = parse_timestamp(events_with_time[0].get('time'))
            last_time = parse_timestamp(events_with_time[-1].get('time'))
            
            self.match.start_time = first_time
            self.match.end_time = last_time
            
            if first_time and last_time:
                duration = last_time - first_time
                logger.info(f"Match duration: {duration}")
    
    def _extract_player_info(self) -> None:
        """Extract player information from player messages."""
        # Extract role assignments
        role_events = [e for e in self.raw_events 
                      if e.get('eventType') == 'playermsg' and e.get('type') == 'RoleAssigned']
        
        for event in role_events:
            player_name = event.get('sourceowner')
            if not player_name:
                continue
                
            role = event.get('itemname')
            team_id = event.get('value1')
            
            if player_name not in self.players:
                player_id = self.player_id_counter
                self.player_id_counter += 1
                self.players[player_name] = Player(
                    player_id=player_id,
                    player_name=player_name,
                    role=role,
                    team_id=team_id
                )
            else:
                # Update existing player
                self.players[player_name].role = role
                self.players[player_name].team_id = team_id
        
        # Extract god selections
        god_events = [e for e in self.raw_events 
                     if e.get('eventType') == 'playermsg' and e.get('type') == 'GodPicked']
        
        for event in god_events:
            player_name = event.get('sourceowner')
            if not player_name:
                continue
                
            god_id = event.get('itemid')
            god_name = event.get('itemname')
            team_id = event.get('value1')
            
            if player_name not in self.players:
                player_id = self.player_id_counter
                self.player_id_counter += 1
                self.players[player_name] = Player(
                    player_id=player_id,
                    player_name=player_name,
                    god_id=god_id,
                    god_name=god_name,
                    team_id=team_id
                )
            else:
                # Update existing player
                self.players[player_name].god_id = god_id
                self.players[player_name].god_name = god_name
                self.players[player_name].team_id = team_id
        
        logger.info(f"Extracted information for {len(self.players)} players.")
    
    def _process_events(self) -> None:
        """Process all events and create the structured event objects."""
        for raw_event in self.raw_events:
            event_type = raw_event.get('eventType')
            event_subtype = raw_event.get('type', 'none')
            
            # Skip already processed start event
            if event_type == 'start':
                continue
                
            # Create the base event
            event = self._create_base_event(raw_event, event_type, event_subtype)
            
            # Process based on event type
            if event_type == 'CombatMsg':
                combat_event = self._process_combat_event(event, raw_event)
                self.combat_events.append(combat_event)
                self.events.append(combat_event)
            elif event_type == 'RewardMsg':
                economy_event = self._process_economy_event(event, raw_event)
                self.economy_events.append(economy_event)
                self.events.append(economy_event)
            elif event_type == 'itemmsg':
                item_event = self._process_item_event(event, raw_event)
                self.item_events.append(item_event)
                self.events.append(item_event)
            elif event_type == 'playermsg':
                player_event = self._process_player_event(event, raw_event)
                self.player_events.append(player_event)
                self.events.append(player_event)
            else:
                # Unknown event type, just add the base event
                self.events.append(event)
    
    def _create_base_event(self, raw_event: Dict[str, Any], event_type: str, event_subtype: str) -> Event:
        """
        Create a base Event object from a raw event.
        
        Args:
            raw_event: The raw event dictionary
            event_type: The event type
            event_subtype: The event subtype
            
        Returns:
            A base Event object
        """
        event_id = self.event_id_counter
        self.event_id_counter += 1
        
        # Extract common fields
        raw_time = raw_event.get('time', '')
        event_timestamp = parse_timestamp(raw_time)
        source_owner = raw_event.get('sourceowner')
        target_owner = raw_event.get('targetowner')
        location_x = safe_parse_numeric(raw_event.get('locationx'))
        location_y = safe_parse_numeric(raw_event.get('locationy'))
        item_id = raw_event.get('itemid')
        item_name = raw_event.get('itemname')
        value1 = raw_event.get('value1')
        value2 = raw_event.get('value2')
        text = raw_event.get('text')
        
        # Convert numeric values if possible
        value1_numeric = safe_parse_numeric(value1)
        value2_numeric = safe_parse_numeric(value2)
        
        # Create player references
        source_player_id = None
        target_player_id = None
        
        if source_owner and source_owner in self.players:
            source_player_id = self.players[source_owner].player_id
            
        if target_owner and target_owner in self.players:
            target_player_id = self.players[target_owner].player_id
            
        # Create the event
        event = Event(
            event_id=event_id,
            event_type=event_type,
            event_subtype=event_subtype,
            raw_time=raw_time,
            event_timestamp=event_timestamp,
            source_owner=source_owner,
            target_owner=target_owner,
            location_x=location_x,
            location_y=location_y,
            item_id=item_id,
            item_name=item_name,
            value1=value1_numeric if value1_numeric is not None else value1,
            value2=value2_numeric if value2_numeric is not None else value2,
            text=text,
            raw_data=raw_event.copy(),
            source_player_id=source_player_id,
            target_player_id=target_player_id,
            match_id=self.match.match_id if self.match else None
        )
        
        return event
    
    def _process_combat_event(self, base_event: Event, raw_event: Dict[str, Any]) -> CombatEvent:
        """
        Process a combat event.
        
        Args:
            base_event: The base Event object
            raw_event: The raw event dictionary
            
        Returns:
            A CombatEvent object
        """
        # Extract combat-specific data
        damage_amount, mitigated_amount = extract_damage_values(raw_event)
        
        # Determine if it's a critical hit
        is_critical = base_event.event_subtype == 'CritDamage'
        
        # Get source and target god names if available
        source_god = None
        target_god = None
        
        if base_event.source_owner and base_event.source_owner in self.players:
            source_god = self.players[base_event.source_owner].god_name
            
        if base_event.target_owner and base_event.target_owner in self.players:
            target_god = self.players[base_event.target_owner].god_name
        
        # Create the combat event
        combat_event = CombatEvent(
            **base_event.__dict__,
            damage_amount=damage_amount,
            mitigated_amount=mitigated_amount,
            is_critical=is_critical,
            ability_id=base_event.item_id,
            ability_name=base_event.item_name,
            source_god=source_god,
            target_god=target_god
        )
        
        return combat_event
    
    def _process_economy_event(self, base_event: Event, raw_event: Dict[str, Any]) -> EconomyEvent:
        """
        Process an economy event.
        
        Args:
            base_event: The base Event object
            raw_event: The raw event dictionary
            
        Returns:
            An EconomyEvent object
        """
        # Extract economy-specific data
        amount, reward_type = extract_reward_values(raw_event)
        
        # Create the economy event
        economy_event = EconomyEvent(
            **base_event.__dict__,
            reward_type=reward_type,
            amount=amount,
            source_type=base_event.value2
        )
        
        return economy_event
    
    def _process_item_event(self, base_event: Event, raw_event: Dict[str, Any]) -> ItemEvent:
        """
        Process an item event.
        
        Args:
            base_event: The base Event object
            raw_event: The raw event dictionary
            
        Returns:
            An ItemEvent object
        """
        # Create a location description
        purchase_location = None
        if base_event.location_x is not None and base_event.location_y is not None:
            purchase_location = f"{base_event.location_x:.1f},{base_event.location_y:.1f}"
        
        # Create the item event
        item_event = ItemEvent(
            **base_event.__dict__,
            purchase_location=purchase_location
        )
        
        return item_event
    
    def _process_player_event(self, base_event: Event, raw_event: Dict[str, Any]) -> PlayerEvent:
        """
        Process a player event.
        
        Args:
            base_event: The base Event object
            raw_event: The raw event dictionary
            
        Returns:
            A PlayerEvent object
        """
        # Extract player-specific data
        god_id = raw_event.get('itemid') if base_event.event_subtype in ['GodHovered', 'GodPicked'] else None
        god_name = raw_event.get('itemname') if base_event.event_subtype in ['GodHovered', 'GodPicked'] else None
        role = raw_event.get('itemname') if base_event.event_subtype == 'RoleAssigned' else None
        
        # Create the player event
        player_event = PlayerEvent(
            **base_event.__dict__,
            god_id=god_id,
            god_name=god_name,
            role=role
        )
        
        return player_event
    
    def classify_entity(self, name: str) -> str:
        """
        Classify an entity as Player, Objective, Jungle Camp, Minion, or Other.
        
        Args:
            name: The entity name to classify
            
        Returns:
            The classification as a string
        """
        if name in self.players:
            return 'Player'
        elif name in self.OBJECTIVES:
            return 'Objective'
        elif name in self.JUNGLE_CAMPS:
            return 'Jungle Camp'
        elif name in self.MINIONS:
            return 'Minion'
        else:
            return 'Other'
    
    def get_combatants_dataframe(self) -> pd.DataFrame:
        """
        Get a DataFrame of all combatants with type classifications.
        
        Returns:
            A pandas DataFrame containing all combatants with classifications
        """
        # Get players dataframe
        players_df = self.get_players_dataframe()
        player_names = set(players_df['player_name'].values)
        
        # Get combat dataframe to find all entities
        combat_df = self.get_combat_dataframe()
        
        # Get unique entity names from combat events (both sources and targets)
        all_sources = set(combat_df['source_owner'].dropna().unique())
        all_targets = set(combat_df['target_owner'].dropna().unique())
        all_entities = all_sources.union(all_targets)
        
        # Create the combatants dataframe
        combatants_data = []
        for entity in all_entities:
            if not entity:  # Skip empty names
                continue
                
            # Classify the entity
            entity_type = self.classify_entity(entity)
            
            # Get player info if it's a player
            player_info = None
            if entity_type == 'Player' and entity in self.players:
                player_info = self.players[entity]
            
            combatants_data.append({
                'name': entity,
                'type': entity_type,
                'player_id': player_info.player_id if player_info else None,
                'god_name': player_info.god_name if player_info else None,
                'team_id': player_info.team_id if player_info else None
            })
        
        # Create the dataframe
        combatants_df = pd.DataFrame(combatants_data)
        
        return combatants_df
    
    def get_enhanced_combat_dataframe(self) -> pd.DataFrame:
        """
        Get a DataFrame of combat events enhanced with entity type classifications.
        
        Returns:
            A pandas DataFrame with source_type and target_type fields added
        """
        # Get the combat dataframe
        combat_df = self.get_combat_dataframe()
        if combat_df.empty:
            return pd.DataFrame()
            
        # Get the combatants dataframe
        combatants_df = self.get_combatants_dataframe()
        if combatants_df.empty:
            return combat_df
        
        # Merge combat dataframe with combatants to add source and target types
        enhanced_combat = combat_df.merge(
            combatants_df[['name', 'type']], 
            left_on='source_owner', 
            right_on='name', 
            how='left'
        ).rename(columns={'type': 'source_type'})
        
        # Drop the redundant 'name' column from the first merge
        if 'name' in enhanced_combat.columns:
            enhanced_combat = enhanced_combat.drop(columns=['name'])
        
        enhanced_combat = enhanced_combat.merge(
            combatants_df[['name', 'type']], 
            left_on='target_owner', 
            right_on='name', 
            how='left'
        ).rename(columns={'type': 'target_type'})
        
        # Drop the redundant 'name' column from the second merge
        if 'name' in enhanced_combat.columns:
            enhanced_combat = enhanced_combat.drop(columns=['name'])
        
        return enhanced_combat
    
    def get_events_dataframe(self) -> pd.DataFrame:
        """
        Get a DataFrame of all events.
        
        Returns:
            A pandas DataFrame containing all events
        """
        if not self.events:
            return pd.DataFrame()
        
        # Convert events to dictionaries
        event_dicts = [event.__dict__ for event in self.events]
        
        # Remove raw_data to avoid large DataFrame
        for event_dict in event_dicts:
            if 'raw_data' in event_dict:
                del event_dict['raw_data']
        
        # Create the DataFrame
        df = pd.DataFrame(event_dicts)
        
        # Sort by timestamp
        if 'event_timestamp' in df.columns:
            df = df.sort_values('event_timestamp')
        
        return df
    
    def get_players_dataframe(self) -> pd.DataFrame:
        """
        Get a DataFrame of all players.
        
        Returns:
            A pandas DataFrame containing all players
        """
        if not self.players:
            return pd.DataFrame()
        
        # Convert players to dictionaries
        player_dicts = [player.__dict__ for player in self.players.values()]
        
        # Create the DataFrame
        df = pd.DataFrame(player_dicts)
        
        return df
    
    def get_combat_dataframe(self) -> pd.DataFrame:
        """
        Get a DataFrame of combat events.
        
        Returns:
            A pandas DataFrame containing combat events
        """
        if not self.combat_events:
            return pd.DataFrame()
        
        # Convert combat events to dictionaries
        event_dicts = [event.__dict__ for event in self.combat_events]
        
        # Remove raw_data to avoid large DataFrame
        for event_dict in event_dicts:
            if 'raw_data' in event_dict:
                del event_dict['raw_data']
        
        # Create the DataFrame
        df = pd.DataFrame(event_dicts)
        
        # Sort by timestamp
        if 'event_timestamp' in df.columns:
            df = df.sort_values('event_timestamp')
        
        return df
    
    def get_economy_dataframe(self) -> pd.DataFrame:
        """
        Get a DataFrame of economy events.
        
        Returns:
            A pandas DataFrame containing economy events
        """
        if not self.economy_events:
            return pd.DataFrame()
        
        # Convert economy events to dictionaries
        event_dicts = [event.__dict__ for event in self.economy_events]
        
        # Remove raw_data to avoid large DataFrame
        for event_dict in event_dicts:
            if 'raw_data' in event_dict:
                del event_dict['raw_data']
        
        # Create the DataFrame
        df = pd.DataFrame(event_dicts)
        
        # Sort by timestamp
        if 'event_timestamp' in df.columns:
            df = df.sort_values('event_timestamp')
        
        return df
    
    def get_item_dataframe(self) -> pd.DataFrame:
        """
        Get a DataFrame of item events.
        
        Returns:
            A pandas DataFrame containing item events
        """
        if not self.item_events:
            return pd.DataFrame()
        
        # Convert item events to dictionaries
        event_dicts = [event.__dict__ for event in self.item_events]
        
        # Remove raw_data to avoid large DataFrame
        for event_dict in event_dicts:
            if 'raw_data' in event_dict:
                del event_dict['raw_data']
        
        # Create the DataFrame
        df = pd.DataFrame(event_dicts)
        
        # Sort by timestamp
        if 'event_timestamp' in df.columns:
            df = df.sort_values('event_timestamp')
        
        return df 