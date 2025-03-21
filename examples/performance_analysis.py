#!/usr/bin/env python
"""
Example script demonstrating how to use the PerformanceAnalyzer.

This script shows how to parse a SMITE 2 CombatLog file and analyze player
performance metrics using the PerformanceAnalyzer.
"""

import os
import sys
import logging
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# Add the parent directory to the path so we can import the src package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.parser import CombatLogParser
from src.analytics.performance import PerformanceAnalyzer
from src.utils.data_validation import records_to_dataframe

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('performance_analyzer.log')
    ]
)
logger = logging.getLogger(__name__)


def analyze_performance(log_file_path):
    """
    Analyze player performance metrics from a SMITE 2 CombatLog file.
    
    Args:
        log_file_path: Path to the CombatLog file
    """
    logger.info(f"Analyzing performance metrics from: {log_file_path}")
    
    # Create and configure the parser
    parser = CombatLogParser()
    parser.parse(log_file_path)
    
    # Create a performance analyzer with default configuration
    analyzer = PerformanceAnalyzer(parser)
    
    # Get the performance metrics
    performance_df = analyzer.to_dataframe()
    
    # Display basic performance metrics
    logger.info("\nPlayer Performance Summary:")
    print("\nPlayer Performance Summary:")
    print("-" * 80)
    summary_cols = ['player_name', 'god_name', 'kills', 'deaths', 'assists', 
                   'kda_ratio', 'player_damage', 'healing_done']
    
    # Only include columns that exist
    available_cols = [col for col in summary_cols if col in performance_df.columns]
    if available_cols:
        print(performance_df[available_cols].to_string(index=False))
    else:
        print("No summary data available.")
    print("-" * 80)
    
    # Get the top performers for different metrics
    print("\nTop 3 Players by KDA:")
    kda_top = analyzer.get_top_performers(metric='kda_ratio', limit=3)
    if not kda_top.empty and 'player_name' in kda_top.columns:
        cols = [col for col in ['player_name', 'god_name', 'kda_ratio'] if col in kda_top.columns]
        print(kda_top[cols].to_string(index=False))
    else:
        print("No KDA data available.")
    
    print("\nTop 3 Players by Player Damage:")
    damage_top = analyzer.get_top_performers(metric='player_damage', limit=3)
    if not damage_top.empty and 'player_name' in damage_top.columns:
        cols = [col for col in ['player_name', 'god_name', 'player_damage'] if col in damage_top.columns]
        print(damage_top[cols].to_string(index=False))
    else:
        print("No damage data available.")
    
    print("\nTop 3 Players by Healing Done:")
    healing_top = analyzer.get_top_performers(metric='healing_done', limit=3)
    if not healing_top.empty and 'player_name' in healing_top.columns:
        cols = [col for col in ['player_name', 'god_name', 'healing_done'] if col in healing_top.columns]
        print(healing_top[cols].to_string(index=False))
    else:
        print("No healing data available.")
    
    # Get analysis results
    results = analyzer.analyze()
    
    # Display players
    if 'players' in results and results['players']:
        print("\nPlayers:")
        for player in results['players']:
            print(f"  {player['player_name']} - {player.get('god_name', 'Unknown')}")
    
    # Try using a different configuration
    print("\nAnalyzing with minimum player damage threshold of 500:")
    analyzer.update_config(min_player_damage=500)
    filtered_df = analyzer.to_dataframe()
    print(f"Players meeting threshold: {len(filtered_df)}")
    if not filtered_df.empty:
        available_cols = [col for col in summary_cols if col in filtered_df.columns]
        if available_cols:
            print(filtered_df[available_cols].to_string(index=False))
    
    return analyzer, results


def generate_visualizations(analyzer, results, output_dir='examples/output'):
    """
    Generate visualizations of player performance metrics.
    
    Args:
        analyzer: PerformanceAnalyzer instance with data
        results: Analysis results from analyzer.analyze()
        output_dir: Directory to save visualizations
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Skip visualization if no data
    if not results or not results.get('kda'):
        logger.warning("No data available for visualization.")
        return
    
    try:
        # Convert analysis results to DataFrames for visualization
        kda_df = records_to_dataframe(results['kda'])
        damage_df = records_to_dataframe(results['damage']) if 'damage' in results else pd.DataFrame()
        
        if kda_df.empty:
            logger.warning("No KDA data available for visualization.")
            return
        
        # 1. KDA Bar Chart
        plt.figure(figsize=(12, 6))
        players = kda_df['player_name'].tolist()
        kills = kda_df['kills'].tolist()
        deaths = kda_df['deaths'].tolist()
        assists = kda_df['assists'].tolist() if 'assists' in kda_df.columns else [0] * len(players)
        
        x = range(len(players))
        width = 0.25
        
        plt.bar([i - width for i in x], kills, width=width, label='Kills', color='green')
        plt.bar(x, deaths, width=width, label='Deaths', color='red')
        plt.bar([i + width for i in x], assists, width=width, label='Assists', color='blue')
        
        plt.xlabel('Players')
        plt.ylabel('Count')
        plt.title('KDA Metrics by Player')
        plt.xticks(x, players, rotation=45)
        plt.legend()
        plt.tight_layout()
        
        plt.savefig(os.path.join(output_dir, 'kda_chart.png'))
        logger.info(f"KDA chart saved to: {os.path.join(output_dir, 'kda_chart.png')}")
        
        # 2. Damage Distribution Pie Chart (if damage data is available)
        if not damage_df.empty:
            # Process each player's damage data
            for _, player in damage_df.iterrows():
                damage_types = ['player_damage', 'objective_damage', 'minion_damage', 'jungle_damage']
                
                # Collect available damage values
                damage_data = []
                damage_labels = []
                
                for damage_type, label in zip(damage_types, 
                                             ['Player Damage', 'Objective Damage', 'Minion Damage', 'Jungle Damage']):
                    if damage_type in damage_df.columns and pd.notna(player.get(damage_type, None)):
                        damage_value = player[damage_type]
                        if damage_value > 0:
                            damage_data.append(damage_value)
                            damage_labels.append(label)
                
                # Skip players with no damage
                if not damage_data or sum(damage_data) == 0:
                    continue
                
                colors = ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99'][:len(damage_data)]
                
                plt.figure(figsize=(8, 8))
                plt.pie(damage_data, labels=damage_labels, colors=colors, autopct='%1.1f%%', startangle=90)
                plt.axis('equal')
                plt.title(f"Damage Distribution for {player['player_name']}")
                
                plt.savefig(os.path.join(output_dir, f"damage_distribution_{player['player_name']}.png"))
                logger.info(f"Damage distribution chart for {player['player_name']} saved.")
            
            # 3. Player Damage Comparison
            if 'player_damage' in damage_df.columns:
                plt.figure(figsize=(12, 6))
                plt.bar(damage_df['player_name'], damage_df['player_damage'], color='purple')
                plt.xlabel('Players')
                plt.ylabel('Damage')
                plt.title('Player Damage Comparison')
                plt.xticks(rotation=45)
                plt.tight_layout()
                
                plt.savefig(os.path.join(output_dir, 'player_damage_comparison.png'))
                logger.info(f"Player damage comparison chart saved.")
        
        print(f"\nVisualizations saved to: {output_dir}")
        
    except Exception as e:
        logger.error(f"Error generating visualizations: {e}")
        print(f"Error generating visualizations: {e}")


if __name__ == "__main__":
    # Check if log file path is provided as argument
    if len(sys.argv) > 1:
        log_file_path = sys.argv[1]
    else:
        # Use the example combat log if no file is specified
        log_file_path = str(Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) / "CombatLogExample.log")
    
    if not os.path.exists(log_file_path):
        print(f"Error: Log file not found at {log_file_path}")
        sys.exit(1)
    
    try:
        # Run the performance analysis
        analyzer, results = analyze_performance(log_file_path)
        
        # Generate visualizations if matplotlib is available
        try:
            generate_visualizations(analyzer, results)
        except ImportError:
            logger.warning("Matplotlib not available. Skipping visualizations.")
            print("Matplotlib not available. Skipping visualizations.")
    
    except Exception as e:
        logger.error(f"Error analyzing performance: {e}")
        print(f"Error analyzing performance: {e}")
        sys.exit(1) 