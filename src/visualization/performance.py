"""
Performance visualization module for SMITE 2 CombatLog visualizations.

This module provides visualization classes for performance metrics such as
KDA, damage, healing, and economy stats.
"""

import os
from typing import Any, Dict, List, Optional, Tuple, Union, cast

import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import numpy as np
import pandas as pd
import seaborn as sns

from src.analytics.performance import PerformanceAnalyzer
from src.utils.logging import get_logger
from src.utils.profiling import profile_time
from src.visualization.base import BaseVisualization, ColorPalette, ThemeManager, PlotUtils
from src.visualization.common import (
    create_kda_bar_chart,
    create_damage_distribution_chart,
    create_player_damage_comparison_chart,
    create_multimetric_radar_chart,
    create_performance_heatmap,
    create_economy_timeline_chart
)

logger = get_logger("visualization.performance")


class KDAVisualization(BaseVisualization):
    """
    Visualization for KDA (Kills, Deaths, Assists) metrics.
    
    This class generates a stacked bar chart showing kills, deaths, and assists
    for each player, sorted by KDA ratio.
    """
    
    def _default_config(self) -> Dict[str, Any]:
        """
        Return the default configuration for the KDA visualization.
        
        Returns:
            Dict[str, Any]: Default configuration parameters
        """
        return {
            'title': 'KDA by Player',
            'figsize': (12, 6),
            'sort_by': 'kda_ratio',
            'use_team_colors': True,
            'player_col': 'player_name',
            'kills_col': 'kills',
            'deaths_col': 'deaths',
            'assists_col': 'assists',
            'team_col': 'team_id',
            'include_kda_ratio': True,
            'theme': 'default'
        }
    
    @profile_time
    def generate(self) -> Figure:
        """
        Generate the KDA visualization.
        
        Returns:
            matplotlib.figure.Figure: The generated figure
        """
        # Get the analyzer data
        df = self.analyzer.to_dataframe()
        
        # Apply the theme
        ThemeManager.apply_theme(self.config['theme'])
        
        # Determine if we should use team colors
        team_col = self.config['team_col'] if self.config['use_team_colors'] and self.config['team_col'] in df.columns else None
        
        # Create the KDA bar chart
        self.figure = create_kda_bar_chart(
            df=df,
            player_col=self.config['player_col'],
            kills_col=self.config['kills_col'],
            deaths_col=self.config['deaths_col'],
            assists_col=self.config['assists_col'],
            title=self.config['title'],
            sort_by=self.config['sort_by'],
            team_col=team_col,
            figsize=self.config['figsize']
        )
        
        # Add a watermark if needed
        if self.config.get('watermark', False):
            PlotUtils.add_watermark(self.figure)
        
        # Reset the theme if needed
        if self.config.get('reset_theme', False):
            ThemeManager.reset_theme()
            
        return self.figure


class DamageDistributionVisualization(BaseVisualization):
    """
    Visualization for damage distribution metrics.
    
    This class generates a stacked bar chart showing different damage types
    (player, objective, minion, jungle) for each player.
    """
    
    def _default_config(self) -> Dict[str, Any]:
        """
        Return the default configuration for the damage distribution visualization.
        
        Returns:
            Dict[str, Any]: Default configuration parameters
        """
        return {
            'title': 'Damage Distribution by Player',
            'figsize': (12, 6),
            'sort_by': 'player_damage',
            'use_team_colors': True,
            'player_col': 'player_name',
            'player_damage_col': 'player_damage',
            'objective_damage_col': 'objective_damage',
            'minion_damage_col': 'minion_damage',
            'jungle_damage_col': 'jungle_damage',
            'team_col': 'team_id',
            'show_percentages': True,
            'theme': 'default'
        }
    
    @profile_time
    def generate(self) -> Figure:
        """
        Generate the damage distribution visualization.
        
        Returns:
            matplotlib.figure.Figure: The generated figure
        """
        # Get the analyzer data
        df = self.analyzer.to_dataframe()
        
        # Apply the theme
        ThemeManager.apply_theme(self.config['theme'])
        
        # Determine if we should use team colors
        team_col = self.config['team_col'] if self.config['use_team_colors'] and self.config['team_col'] in df.columns else None
        
        # Create the damage distribution chart
        self.figure = create_damage_distribution_chart(
            df=df,
            player_col=self.config['player_col'],
            player_damage_col=self.config['player_damage_col'],
            objective_damage_col=self.config['objective_damage_col'],
            minion_damage_col=self.config['minion_damage_col'],
            jungle_damage_col=self.config['jungle_damage_col'],
            title=self.config['title'],
            sort_by=self.config['sort_by'],
            team_col=team_col,
            figsize=self.config['figsize']
        )
        
        # Add a watermark if needed
        if self.config.get('watermark', False):
            PlotUtils.add_watermark(self.figure)
        
        # Reset the theme if needed
        if self.config.get('reset_theme', False):
            ThemeManager.reset_theme()
            
        return self.figure


class PlayerDamageComparisonVisualization(BaseVisualization):
    """
    Visualization for player damage comparison metrics.
    
    This class generates a bar chart comparing player damage with an optional
    damage per minute (DPM) overlay.
    """
    
    def _default_config(self) -> Dict[str, Any]:
        """
        Return the default configuration for the player damage comparison visualization.
        
        Returns:
            Dict[str, Any]: Default configuration parameters
        """
        return {
            'title': 'Player Damage Comparison',
            'figsize': (12, 6),
            'sort_by': 'player_damage',
            'use_team_colors': True,
            'player_col': 'player_name',
            'damage_col': 'player_damage',
            'dpm_col': 'damage_per_minute',
            'team_col': 'team_id',
            'show_average': True,
            'theme': 'default'
        }
    
    @profile_time
    def generate(self) -> Figure:
        """
        Generate the player damage comparison visualization.
        
        Returns:
            matplotlib.figure.Figure: The generated figure
        """
        # Get the analyzer data
        df = self.analyzer.to_dataframe()
        
        # Apply the theme
        ThemeManager.apply_theme(self.config['theme'])
        
        # Determine if we should use team colors
        team_col = self.config['team_col'] if self.config['use_team_colors'] and self.config['team_col'] in df.columns else None
        
        # Determine if we should include DPM
        dpm_col = self.config['dpm_col'] if self.config['dpm_col'] in df.columns else None
        
        # Create the player damage comparison chart
        self.figure = create_player_damage_comparison_chart(
            df=df,
            player_col=self.config['player_col'],
            damage_col=self.config['damage_col'],
            dpm_col=dpm_col,
            title=self.config['title'],
            sort_by=self.config['sort_by'],
            team_col=team_col,
            figsize=self.config['figsize']
        )
        
        # Add a watermark if needed
        if self.config.get('watermark', False):
            PlotUtils.add_watermark(self.figure)
        
        # Reset the theme if needed
        if self.config.get('reset_theme', False):
            ThemeManager.reset_theme()
            
        return self.figure


class PerformanceRadarVisualization(BaseVisualization):
    """
    Visualization for multi-metric performance radar charts.
    
    This class generates radar charts for each player showing normalized performance
    across multiple metrics.
    """
    
    def _default_config(self) -> Dict[str, Any]:
        """
        Return the default configuration for the performance radar visualization.
        
        Returns:
            Dict[str, Any]: Default configuration parameters
        """
        return {
            'title': 'Player Performance Radar',
            'figsize': (14, 10),
            'metrics': ['kills', 'deaths', 'assists', 'player_damage', 'healing_done', 'gold_earned'],
            'player_col': 'player_name',
            'n_players': 10,
            'theme': 'default'
        }
    
    @profile_time
    def generate(self) -> Figure:
        """
        Generate the performance radar visualization.
        
        Returns:
            matplotlib.figure.Figure: The generated figure
        """
        # Get the analyzer data
        df = self.analyzer.to_dataframe()
        
        # Apply the theme
        ThemeManager.apply_theme(self.config['theme'])
        
        # Create the multi-metric radar chart
        self.figure = create_multimetric_radar_chart(
            df=df,
            player_col=self.config['player_col'],
            metrics=self.config['metrics'],
            title=self.config['title'],
            n_players=self.config['n_players'],
            figsize=self.config['figsize']
        )
        
        # Add a watermark if needed
        if self.config.get('watermark', False):
            PlotUtils.add_watermark(self.figure)
        
        # Reset the theme if needed
        if self.config.get('reset_theme', False):
            ThemeManager.reset_theme()
            
        return self.figure


class PerformanceHeatmapVisualization(BaseVisualization):
    """
    Visualization for performance heatmap.
    
    This class generates a heatmap showing normalized performance metrics
    across players.
    """
    
    def _default_config(self) -> Dict[str, Any]:
        """
        Return the default configuration for the performance heatmap visualization.
        
        Returns:
            Dict[str, Any]: Default configuration parameters
        """
        return {
            'title': 'Performance Metrics Heatmap',
            'figsize': (12, 8),
            'metrics': ['kills', 'deaths', 'assists', 'player_damage', 'healing_done', 'gold_earned'],
            'player_col': 'player_name',
            'cmap': 'viridis',
            'theme': 'default'
        }
    
    @profile_time
    def generate(self) -> Figure:
        """
        Generate the performance heatmap visualization.
        
        Returns:
            matplotlib.figure.Figure: The generated figure
        """
        # Get the analyzer data
        df = self.analyzer.to_dataframe()
        
        # Apply the theme
        ThemeManager.apply_theme(self.config['theme'])
        
        # Create the performance heatmap
        self.figure = create_performance_heatmap(
            df=df,
            player_col=self.config['player_col'],
            metrics=self.config['metrics'],
            title=self.config['title'],
            cmap=self.config['cmap'],
            figsize=self.config['figsize']
        )
        
        # Add a watermark if needed
        if self.config.get('watermark', False):
            PlotUtils.add_watermark(self.figure)
        
        # Reset the theme if needed
        if self.config.get('reset_theme', False):
            ThemeManager.reset_theme()
            
        return self.figure


class PerformanceVisualizer:
    """
    Factory class for performance visualizations.
    
    This class provides methods to create various performance visualizations
    from a PerformanceAnalyzer instance.
    """
    
    def __init__(self, analyzer: PerformanceAnalyzer):
        """
        Initialize the performance visualizer.
        
        Args:
            analyzer: The PerformanceAnalyzer instance containing the data
        """
        self.analyzer = analyzer
    
    def create_kda_chart(self, **config) -> KDAVisualization:
        """
        Create a KDA visualization.
        
        Args:
            **config: Optional configuration parameters
            
        Returns:
            KDAVisualization: The KDA visualization instance
        """
        return KDAVisualization(self.analyzer, config)
    
    def create_damage_distribution(self, **config) -> DamageDistributionVisualization:
        """
        Create a damage distribution visualization.
        
        Args:
            **config: Optional configuration parameters
            
        Returns:
            DamageDistributionVisualization: The damage distribution visualization instance
        """
        return DamageDistributionVisualization(self.analyzer, config)
    
    def create_player_damage_comparison(self, **config) -> PlayerDamageComparisonVisualization:
        """
        Create a player damage comparison visualization.
        
        Args:
            **config: Optional configuration parameters
            
        Returns:
            PlayerDamageComparisonVisualization: The player damage comparison visualization instance
        """
        return PlayerDamageComparisonVisualization(self.analyzer, config)
    
    def create_performance_radar(self, **config) -> PerformanceRadarVisualization:
        """
        Create a performance radar visualization.
        
        Args:
            **config: Optional configuration parameters
            
        Returns:
            PerformanceRadarVisualization: The performance radar visualization instance
        """
        return PerformanceRadarVisualization(self.analyzer, config)
    
    def create_performance_heatmap(self, **config) -> PerformanceHeatmapVisualization:
        """
        Create a performance heatmap visualization.
        
        Args:
            **config: Optional configuration parameters
            
        Returns:
            PerformanceHeatmapVisualization: The performance heatmap visualization instance
        """
        return PerformanceHeatmapVisualization(self.analyzer, config)
    
    def generate_all(self, output_dir: Optional[str] = None, 
                    formats: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Generate all performance visualizations.
        
        Args:
            output_dir: Optional directory to save the visualizations
            formats: Optional list of formats to save the visualizations in
            
        Returns:
            Dict[str, Any]: Dictionary of visualization names to figures or file paths
        """
        logger.info("Generating all performance visualizations")
        
        # Default format is PNG
        formats = formats or ['png']
        
        # Create the visualizations
        visualizations = {
            'kda_chart': self.create_kda_chart(),
            'damage_distribution': self.create_damage_distribution(),
            'player_damage_comparison': self.create_player_damage_comparison(),
            'performance_radar': self.create_performance_radar(),
            'performance_heatmap': self.create_performance_heatmap()
        }
        
        results = {}
        
        # Generate and export the visualizations
        for name, viz in visualizations.items():
            try:
                figure = viz.generate()
                
                # Export the visualization if an output directory is specified
                if output_dir:
                    # Create the output directory if it doesn't exist
                    os.makedirs(output_dir, exist_ok=True)
                    
                    # Export the visualization in each requested format
                    paths = []
                    for fmt in formats:
                        path = viz.export(os.path.join(output_dir, name), format=fmt)
                        paths.append(path)
                    
                    results[name] = paths
                else:
                    results[name] = figure
                    
                # Close the figure to free memory
                viz.close()
                
            except Exception as e:
                logger.error(f"Error generating {name} visualization: {str(e)}")
                results[name] = None
        
        logger.info(f"Generated {len(results)} performance visualizations")
        return results 