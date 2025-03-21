#!/usr/bin/env python
"""
Enhanced example script demonstrating performance analysis visualizations.

This script shows how to use the PerformanceAnalyzer with the new visualization
framework to generate a variety of visualizations from CombatLog data.
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
from src.visualization.performance import PerformanceVisualizer
from src.visualization.base import ThemeManager
from src.utils.logging import get_logger

# Set up logging
logger = get_logger("examples.enhanced_visualization")


def run_enhanced_visualization(log_file_path, output_dir='examples/output'):
    """
    Run enhanced visualizations on a SMITE 2 CombatLog file.
    
    Args:
        log_file_path: Path to the CombatLog file
        output_dir: Directory to save visualization outputs
    """
    logger.info(f"Running enhanced visualization on: {log_file_path}")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Create and configure the parser
    parser = CombatLogParser()
    parser.parse(log_file_path)
    
    # Create a performance analyzer
    analyzer = PerformanceAnalyzer(parser)
    
    # Create a performance visualizer
    visualizer = PerformanceVisualizer(analyzer)
    
    # Generate all visualizations and save them to the output directory
    results = visualizer.generate_all(output_dir=output_dir, formats=['png', 'svg'])
    
    # Print the results
    print("\nGenerated Visualizations:")
    print("-" * 80)
    for name, paths in results.items():
        if paths:
            path_list = ", ".join([os.path.basename(p) for p in paths])
            print(f"{name}: {path_list}")
        else:
            print(f"{name}: Error generating visualization")
    print("-" * 80)
    
    # Also demonstrate individual visualizations with custom configurations
    print("\nGenerating Custom Visualizations:")
    
    # Custom KDA chart with dark theme
    print("- Custom KDA chart with dark theme")
    ThemeManager.apply_theme('dark')
    kda_viz = visualizer.create_kda_chart(
        title="Player KDA (Dark Theme)",
        figsize=(14, 7)
    )
    kda_fig = kda_viz.generate()
    kda_viz.export(os.path.join(output_dir, "custom_kda_dark"), format='png')
    kda_viz.close()
    ThemeManager.reset_theme()
    
    # Custom damage distribution with sorted by total damage
    print("- Custom damage distribution (sorted by total damage)")
    damage_viz = visualizer.create_damage_distribution(
        title="Damage Distribution (Sorted by Total)",
        sort_by='total_damage' if 'total_damage' in analyzer.to_dataframe().columns else 'player_damage'
    )
    damage_fig = damage_viz.generate()
    damage_viz.export(os.path.join(output_dir, "custom_damage_distribution"), format='png')
    damage_viz.close()
    
    # Custom performance radar with selected metrics
    print("- Custom performance radar with selected metrics")
    metrics = ['kills', 'deaths', 'assists', 'player_damage', 'healing_done']
    # Make sure all metrics exist in the data
    available_metrics = [m for m in metrics if m in analyzer.to_dataframe().columns]
    
    radar_viz = visualizer.create_performance_radar(
        title="Core Combat Metrics Radar",
        metrics=available_metrics,
        figsize=(16, 12)
    )
    radar_fig = radar_viz.generate()
    radar_viz.export(os.path.join(output_dir, "custom_performance_radar"), format='png')
    radar_viz.close()
    
    # Custom performance heatmap with 'plasma' colormap
    print("- Custom performance heatmap with plasma colormap")
    heatmap_viz = visualizer.create_performance_heatmap(
        title="Performance Metrics Heatmap (Plasma)",
        cmap='plasma'
    )
    heatmap_fig = heatmap_viz.generate()
    heatmap_viz.export(os.path.join(output_dir, "custom_performance_heatmap"), format='png')
    heatmap_viz.close()
    
    print(f"\nAll visualizations saved to: {output_dir}")
    return analyzer


def analyze_performance_metrics(analyzer):
    """
    Analyze and print performance metrics from the analyzer.
    
    Args:
        analyzer: The PerformanceAnalyzer instance
    """
    print("\nPerformance Metrics Summary:")
    print("-" * 80)
    
    # Get the dataframe with all metrics
    df = analyzer.to_dataframe()
    
    # Display a summary of key metrics
    summary_cols = ['player_name', 'god_name', 'kills', 'deaths', 'assists', 
                   'kda_ratio', 'player_damage', 'healing_done']
    
    # Ensure all columns exist
    available_cols = [col for col in summary_cols if col in df.columns]
    if available_cols:
        print(df[available_cols].to_string(index=False))
    
    # Get top performers for different metrics
    print("\nTop Performers:")
    metrics = ['kda_ratio', 'player_damage', 'healing_done', 'gold_earned']
    
    for metric in metrics:
        if metric in df.columns:
            try:
                top = analyzer.get_top_performers(metric=metric, limit=3)
                if not top.empty:
                    print(f"\nTop 3 by {metric.replace('_', ' ').title()}:")
                    display_cols = ['player_name', 'god_name', metric]
                    print(top[display_cols].to_string(index=False))
            except Exception as e:
                logger.warning(f"Error getting top performers for {metric}: {e}")
    
    print("-" * 80)


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
        # Run the enhanced visualization
        analyzer = run_enhanced_visualization(log_file_path)
        
        # Analyze the performance metrics
        analyze_performance_metrics(analyzer)
        
    except Exception as e:
        logger.error(f"Error in enhanced visualization: {e}", exc_info=True)
        print(f"Error in enhanced visualization: {e}")
        sys.exit(1) 