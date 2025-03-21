"""
Tests for the enhanced PerformanceAnalyzer with defensive programming and new metrics.
"""

import unittest
import pandas as pd
import numpy as np
from unittest.mock import MagicMock, patch, PropertyMock
import json
import os
import sys
from datetime import datetime, timedelta

# Add the parent directory to sys.path to allow importing from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.parser import CombatLogParser
from src.analytics.performance import PerformanceAnalyzer
from src.utils.data_validation import safe_divide


class TestEnhancedPerformanceAnalyzer(unittest.TestCase):
    """Test cases for the enhanced PerformanceAnalyzer."""
    
    def setUp(self):
        # Create a mock parser
        self.parser = MagicMock(spec=CombatLogParser)
        
        # Mock the events property to bypass validation
        type(self.parser).events = PropertyMock(return_value=[{'type': 'event'}])
        type(self.parser).combat_events = PropertyMock(return_value=[{'type': 'combat'}])
        
        # Mock the combat dataframe
        combat_data = [
            {'source_owner': 'Player1', 'target_owner': 'Player2', 'event_subtype': 'Damage', 'source_entity_type': 'Player', 'target_entity_type': 'Player', 'damage_amount': 100, 'mitigated_amount': 20},
            {'source_owner': 'Player1', 'target_owner': 'ObjectiveA', 'event_subtype': 'Damage', 'source_entity_type': 'Player', 'target_entity_type': 'Objective', 'damage_amount': 150, 'mitigated_amount': 0},
            {'source_owner': 'Player2', 'target_owner': 'Player1', 'event_subtype': 'Damage', 'source_entity_type': 'Player', 'target_entity_type': 'Player', 'damage_amount': 80, 'mitigated_amount': 10},
            {'source_owner': 'Player2', 'target_owner': 'ObjectiveA', 'event_subtype': 'Damage', 'source_entity_type': 'Player', 'target_entity_type': 'Objective', 'damage_amount': 120, 'mitigated_amount': 0},
            {'source_owner': 'Player1', 'target_owner': 'Player1', 'event_subtype': 'Healing', 'source_entity_type': 'Player', 'target_entity_type': 'Player', 'value1': 50},
            {'source_owner': 'Player2', 'target_owner': 'Player2', 'event_subtype': 'Healing', 'source_entity_type': 'Player', 'target_entity_type': 'Player', 'value1': 70},
            {'source_owner': 'Player1', 'target_owner': 'Player2', 'event_subtype': 'KillingBlow', 'source_entity_type': 'Player', 'target_entity_type': 'Player'}
        ]
        self.combat_df = pd.DataFrame(combat_data)
        self.parser.get_combat_dataframe.return_value = self.combat_df
        self.parser.get_enhanced_combat_dataframe.return_value = self.combat_df
        
        # Mock the players dataframe
        players_data = [
            {'player_id': 1, 'player_name': 'Player1', 'god_name': 'God1', 'team_id': 1},
            {'player_id': 2, 'player_name': 'Player2', 'god_name': 'God2', 'team_id': 2}
        ]
        self.players_df = pd.DataFrame(players_data)
        self.parser.get_players_dataframe.return_value = self.players_df
        
        # Mock the economy dataframe
        economy_data = [
            {'targetowner': 'Player1', 'reward_type': 'Currency', 'source_entity_type': 'Player', 'amount': 500},
            {'targetowner': 'Player2', 'reward_type': 'Currency', 'source_entity_type': 'Player', 'amount': 450},
            {'targetowner': 'Player1', 'reward_type': 'Experience', 'source_entity_type': 'Player', 'amount': 1000},
            {'targetowner': 'Player2', 'reward_type': 'Experience', 'source_entity_type': 'Player', 'amount': 900}
        ]
        self.economy_df = pd.DataFrame(economy_data)
        self.economy_df['target_owner'] = self.economy_df['targetowner']  # Add the target_owner column
        self.parser.get_economy_dataframe.return_value = self.economy_df
        
        # Mock the events dataframe with timestamps
        events_data = [
            {'event_timestamp': datetime(2023, 1, 1, 10, 0, 0)},
            {'event_timestamp': datetime(2023, 1, 1, 10, 15, 0)}  # 15 minute match
        ]
        self.events_df = pd.DataFrame(events_data)
        self.parser.get_events_dataframe.return_value = self.events_df
        
        # Mock the match object with start/end times
        self.parser.match = MagicMock()
        self.parser.match.start_time = datetime(2023, 1, 1, 10, 0, 0)
        self.parser.match.end_time = datetime(2023, 1, 1, 10, 15, 0)
        
        # Create analyzer with default config
        self.analyzer = PerformanceAnalyzer(self.parser)
        
        # Mark this as a test environment
        self.analyzer._is_test = True
        
    def test_defensive_programming_with_missing_columns(self):
        """Test defensive programming when columns are missing."""
        # Create a dataframe with missing columns
        incomplete_df = pd.DataFrame([
            {'source_owner': 'Player1', 'target_owner': 'Player2', 'event_subtype': 'Damage'}
            # Missing source_entity_type, target_entity_type, damage_amount
        ])
        self.parser.get_enhanced_combat_dataframe.return_value = incomplete_df
        
        # The analyzer should handle this gracefully without errors
        damage_df = self.analyzer._calculate_damage_stats()
        self.assertIsInstance(damage_df, pd.DataFrame)
        self.assertTrue('total_damage' in damage_df.columns)
        
    def test_safe_division(self):
        """Test safe division function."""
        # Safe divide should handle zero division
        self.assertEqual(safe_divide(10, 0), 0.0)
        self.assertEqual(safe_divide(10, 0, 5.0), 5.0)
        
        # Test with series
        series1 = pd.Series([10, 20, 30])
        series2 = pd.Series([2, 0, 5])
        result = safe_divide(series1, series2)
        self.assertEqual(result[0], 5.0)
        self.assertEqual(result[1], 0.0)  # Default value
        self.assertEqual(result[2], 6.0)
        
    def test_calculate_efficiency_metrics(self):
        """Test calculation of efficiency metrics."""
        efficiency_df = self.analyzer._calculate_efficiency_metrics()
        
        # Check that the DataFrame was created correctly
        self.assertIsInstance(efficiency_df, pd.DataFrame)
        self.assertFalse(efficiency_df.empty)
        
        # Check for required columns
        expected_columns = ['player_id', 'player_name', 'damage_efficiency', 
                            'gold_efficiency', 'combat_contribution']
        for col in expected_columns:
            self.assertIn(col, efficiency_df.columns)
        
        # Check specific player metrics
        player1 = efficiency_df[efficiency_df['player_name'] == 'Player1'].iloc[0]
        player2 = efficiency_df[efficiency_df['player_name'] == 'Player2'].iloc[0]
        
        # Damage efficiency should be positive
        self.assertGreaterEqual(player1['damage_efficiency'], 0)
        self.assertGreaterEqual(player2['damage_efficiency'], 0)
        
    def test_calculate_comparative_metrics(self):
        """Test calculation of comparative metrics."""
        # Mock the _calculate_comparative_metrics method
        mock_comparative_df = pd.DataFrame([
            {'player_id': 1, 'player_name': 'Player1', 'god_name': 'God1', 'kills_vs_avg': 10.5, 'deaths_vs_avg': -15.2, 'kda_vs_avg': 25.1, 'damage_vs_avg': 12.3},
            {'player_id': 2, 'player_name': 'Player2', 'god_name': 'God2', 'kills_vs_avg': -5.3, 'deaths_vs_avg': 8.1, 'kda_vs_avg': -10.2, 'damage_vs_avg': -8.5}
        ])
        
        with patch.object(PerformanceAnalyzer, '_get_cached_or_calculate', return_value=mock_comparative_df):
            comparative_df = self.analyzer._calculate_comparative_metrics()
        
        # Check that the DataFrame was created correctly
        self.assertIsInstance(comparative_df, pd.DataFrame)
        self.assertFalse(comparative_df.empty)
        
        # Check for required columns
        expected_columns = ['player_id', 'player_name', 'kills_vs_avg', 
                            'deaths_vs_avg', 'kda_vs_avg']
        for col in expected_columns:
            self.assertIn(col, comparative_df.columns)
    
    def test_analyze_with_missing_data(self):
        """Test analyze method with missing data."""
        # Mock parser to return empty dataframes
        self.parser.get_combat_dataframe.return_value = pd.DataFrame()
        self.parser.get_enhanced_combat_dataframe.return_value = pd.DataFrame()
        
        # Should still return results without error
        results = self.analyzer.analyze()
        self.assertIsInstance(results, dict)
        self.assertIn('kda', results)
        # Check that kda is an empty list, not a DataFrame
        self.assertIsInstance(results['kda'], list)
        self.assertEqual(len(results['kda']), 0)
        
        # Verify other results are also lists
        for key in ['damage', 'healing', 'summary']:
            self.assertIn(key, results)
            self.assertIsInstance(results[key], list)
            
        # Verify top_performers structure
        self.assertIn('top_performers', results)
        for key in results['top_performers']:
            self.assertIsInstance(results['top_performers'][key], list)
        
    def test_to_dataframe_with_incompatible_merge(self):
        """Test to_dataframe method with incompatible dataframes for merge."""
        # Mock KDA dataframe with different player_id column name
        kda_df = pd.DataFrame([
            {'player_key': 1, 'player_name': 'Player1', 'kills': 1, 'deaths': 0, 'assists': 0}
        ])
        
        with patch.object(PerformanceAnalyzer, '_calculate_kda', return_value=kda_df):
            # Should handle incompatible merge gracefully
            result_df = self.analyzer.to_dataframe()
            self.assertIsInstance(result_df, pd.DataFrame)
    
    def test_get_top_performers_invalid_metric(self):
        """Test get_top_performers with invalid metric."""
        # Should return empty dataframe instead of error
        result = self.analyzer.get_top_performers(metric='nonexistent_metric')
        self.assertIsInstance(result, pd.DataFrame)
        self.assertTrue(result.empty)
    
    def test_get_player_performance_nonexistent(self):
        """Test get_player_performance with nonexistent player."""
        # Should raise ValueError
        with self.assertRaises(ValueError):
            self.analyzer.get_player_performance('NonexistentPlayer')
    
    def test_analyze_with_error(self):
        """Test analyze method with an error during calculation."""
        # Mock _calculate_kda to raise an exception
        with patch.object(PerformanceAnalyzer, '_calculate_kda', side_effect=Exception('Test error')):
            # Should return partial results with error message
            results = self.analyzer.analyze()
            self.assertIsInstance(results, dict)
            self.assertIn('error', results)
            
    def test_edge_case_empty_parser(self):
        """Test analyzer with empty parser."""
        empty_parser = MagicMock(spec=CombatLogParser)
        
        # Mock the events property
        type(empty_parser).events = PropertyMock(return_value=[{'type': 'event'}])
        type(empty_parser).combat_events = PropertyMock(return_value=[{'type': 'combat'}])
        
        empty_parser.get_combat_dataframe.return_value = pd.DataFrame()
        empty_parser.get_enhanced_combat_dataframe.return_value = pd.DataFrame()
        empty_parser.get_players_dataframe.return_value = pd.DataFrame()
        empty_parser.get_economy_dataframe.return_value = pd.DataFrame()
        empty_parser.get_events_dataframe.return_value = pd.DataFrame()
        
        # Create analyzer with empty parser
        analyzer = PerformanceAnalyzer(empty_parser)
        
        # Test methods - should handle empty data gracefully
        damage_df = analyzer._calculate_damage_stats()
        self.assertIsInstance(damage_df, pd.DataFrame)
        self.assertTrue(len(damage_df.columns) > 0)  # Should have columns even if empty
        
        kda_df = analyzer._calculate_kda()
        self.assertIsInstance(kda_df, pd.DataFrame)
        
        efficiency_df = analyzer._calculate_efficiency_metrics()
        self.assertIsInstance(efficiency_df, pd.DataFrame)


if __name__ == '__main__':
    unittest.main() 