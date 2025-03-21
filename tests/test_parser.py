"""
Test script for the SMITE 2 CombatLog Parser.

This script tests the basic functionality of the parser by parsing a log file
and printing some statistics about the parsed data.
"""

import os
import sys
import logging
from datetime import datetime
import pytest

# Add the parent directory to the path so we can import the src module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.parser import CombatLogParser

# Add log_file fixture at the top of the file
@pytest.fixture
def log_file():
    """Fixture to provide a path to a sample log file."""
    # Use the sample file in the tests directory
    sample_path = os.path.join(os.path.dirname(__file__), 'sample_combat_log.txt')
    if not os.path.exists(sample_path):
        # Create a minimal sample file if it doesn't exist
        with open(sample_path, 'w') as f:
            f.write('{"Type": "CombatLog", "Mode": "Test", "Events": []}\n')
    return sample_path

def test_parser(log_file):
    """Test parser initialization and loading."""
    parser = CombatLogParser()
    assert os.path.exists(log_file), f"Log file not found: {log_file}"
    parser.parse(log_file)
    
    # Check that we have events
    assert hasattr(parser, 'events'), "Parser missing events attribute"
    
    # Check that we have the right attributes
    assert hasattr(parser, 'match'), "Parser missing match attribute"
    assert parser.match is not None, "Parser match is None"

    # Print some basic statistics
    print("\n=== MATCH INFORMATION ===")
    if parser.match:
        print(f"Match ID: {parser.match.match_id}")
        print(f"Log Mode: {parser.match.log_mode}")
        if parser.match.start_time and parser.match.end_time:
            duration = parser.match.end_time - parser.match.start_time
            print(f"Duration: {duration}")
    
    print("\n=== PLAYER INFORMATION ===")
    print(f"Total Players: {len(parser.players)}")
    for player_name, player in parser.players.items():
        print(f"Player: {player_name}, God: {player.god_name}, Role: {player.role}, Team: {player.team_id}")
    
    print("\n=== EVENT STATISTICS ===")
    print(f"Total Events: {len(parser.events)}")
    print(f"Combat Events: {len(parser.combat_events)}")
    print(f"Economy Events: {len(parser.economy_events)}")
    print(f"Item Events: {len(parser.item_events)}")
    print(f"Player Events: {len(parser.player_events)}")
    
    # Print sample events from each category
    if parser.combat_events:
        print("\n=== SAMPLE COMBAT EVENT ===")
        event = parser.combat_events[0]
        print(f"Event ID: {event.event_id}")
        print(f"Type: {event.event_type} - {event.event_subtype}")
        print(f"Time: {event.event_timestamp}")
        print(f"Source: {event.source_owner} (God: {event.source_god})")
        print(f"Target: {event.target_owner} (God: {event.target_god})")
        print(f"Ability: {event.ability_name} (ID: {event.ability_id})")
        print(f"Damage: {event.damage_amount}, Mitigated: {event.mitigated_amount}")
        print(f"Critical: {event.is_critical}")
        print(f"Location: ({event.location_x}, {event.location_y})")
        print(f"Text: {event.text}")
    
    if parser.economy_events:
        print("\n=== SAMPLE ECONOMY EVENT ===")
        event = parser.economy_events[0]
        print(f"Event ID: {event.event_id}")
        print(f"Type: {event.event_type} - {event.event_subtype}")
        print(f"Time: {event.event_timestamp}")
        print(f"Source: {event.source_owner}")
        print(f"Target: {event.target_owner}")
        print(f"Reward Type: {event.reward_type}")
        print(f"Amount: {event.amount}")
        print(f"Source Type: {event.source_type}")
        print(f"Location: ({event.location_x}, {event.location_y})")
        print(f"Text: {event.text}")
    
    if parser.item_events:
        print("\n=== SAMPLE ITEM EVENT ===")
        event = parser.item_events[0]
        print(f"Event ID: {event.event_id}")
        print(f"Type: {event.event_type} - {event.event_subtype}")
        print(f"Time: {event.event_timestamp}")
        print(f"Player: {event.source_owner}")
        print(f"Item: {event.item_name} (ID: {event.item_id})")
        print(f"Location: {event.purchase_location}")
        print(f"Text: {event.text}")
    
    # Test DataFrame generation
    try:
        # Generate DataFrames
        events_df = parser.get_events_dataframe()
        players_df = parser.get_players_dataframe()
        combat_df = parser.get_combat_dataframe()
        economy_df = parser.get_economy_dataframe()
        item_df = parser.get_item_dataframe()
        
        # Print DataFrame shapes
        print("\n=== DATAFRAME STATISTICS ===")
        print(f"Events DataFrame: {events_df.shape[0]} rows, {events_df.shape[1]} columns")
        print(f"Players DataFrame: {players_df.shape[0]} rows, {players_df.shape[1]} columns")
        print(f"Combat DataFrame: {combat_df.shape[0]} rows, {combat_df.shape[1]} columns")
        print(f"Economy DataFrame: {economy_df.shape[0]} rows, {economy_df.shape[1]} columns")
        print(f"Item DataFrame: {item_df.shape[0]} rows, {item_df.shape[1]} columns")
        
        # Test combatants functionality
        combatants_df = parser.get_combatants_dataframe()
        enhanced_combat_df = parser.get_enhanced_combat_dataframe()
        
        print(f"Combatants DataFrame: {combatants_df.shape[0]} rows, {combatants_df.shape[1]} columns")
        print(f"Enhanced Combat DataFrame: {enhanced_combat_df.shape[0]} rows, {enhanced_combat_df.shape[1]} columns")
        
        # Print combatant types
        if not combatants_df.empty:
            print("\n=== COMBATANT TYPES ===")
            type_counts = combatants_df['type'].value_counts()
            for entity_type, count in type_counts.items():
                print(f"{entity_type}: {count} entities")
                
            # Print a few combatants of each type
            print("\n=== SAMPLE COMBATANTS BY TYPE ===")
            for entity_type in type_counts.index:
                entities = combatants_df[combatants_df['type'] == entity_type]['name'].values[:2]
                print(f"{entity_type}: {', '.join(entities)}")
        
        # Sample query - Top damage dealers
        if not combat_df.empty:
            damage_by_player = combat_df[combat_df['damage_amount'].notna()].groupby('source_owner')['damage_amount'].sum().sort_values(ascending=False)
            
            print("\n=== TOP DAMAGE DEALERS ===")
            for player, damage in damage_by_player.head(5).items():
                print(f"{player}: {damage:.0f} damage")
        
        # Sample query - Gold earned by player
        if not economy_df.empty and 'gold' in economy_df['reward_type'].values:
            gold_df = economy_df[economy_df['reward_type'] == 'gold']
            gold_by_player = gold_df.groupby('target_owner')['amount'].sum().sort_values(ascending=False)
            
            print("\n=== GOLD EARNED BY PLAYER ===")
            for player, gold in gold_by_player.head(5).items():
                print(f"{player}: {gold:.0f} gold")
        
        # Sample query - Item build order for a player
        if not item_df.empty and len(parser.players) > 0:
            # Pick the first player with the most items
            items_by_player = item_df.groupby('source_owner').size().sort_values(ascending=False)
            if not items_by_player.empty:
                sample_player = items_by_player.index[0]
                player_items = item_df[item_df['source_owner'] == sample_player].sort_values('event_timestamp')
                
                print(f"\n=== ITEM BUILD FOR {sample_player} ===")
                for _, item in player_items.iterrows():
                    timestamp = item['event_timestamp']
                    item_name = item['item_name']
                    if timestamp and item_name:
                        time_str = timestamp.strftime('%H:%M:%S')
                        print(f"{time_str}: {item_name}")
        
        # Sample query with enhanced combat dataframe
        if not enhanced_combat_df.empty:
            # Player vs Player damage
            pvp_damage = enhanced_combat_df[
                (enhanced_combat_df['source_type'] == 'Player') & 
                (enhanced_combat_df['target_type'] == 'Player') &
                (enhanced_combat_df['damage_amount'].notna())
            ]
            
            if not pvp_damage.empty:
                print("\n=== PLAYER VS PLAYER DAMAGE ===")
                pvp_by_player = pvp_damage.groupby('source_owner')['damage_amount'].sum().sort_values(ascending=False)
                for player, damage in pvp_by_player.items():
                    print(f"{player}: {damage:.0f} PvP damage")
        
    except Exception as e:
        print(f"Error generating DataFrames: {e}")
    
    print("\nParser test completed successfully.")


if __name__ == "__main__":
    # Get the log file path from the command line, or use the default
    log_file = sys.argv[1] if len(sys.argv) > 1 else "CombatLogExample.log"
    
    # Test the parser
    test_parser(log_file)
    
    # Exit with an appropriate code
    sys.exit(0) 