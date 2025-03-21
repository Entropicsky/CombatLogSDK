"""
Common visualization utilities for SMITE 2 CombatLog Parser.

This module provides common visualization functions that can be used
across different visualization types.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mplcolors
from matplotlib.figure import Figure
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import seaborn as sns
from typing import Any, Dict, List, Optional, Tuple, Union, Callable, cast

from src.utils.logging import get_logger
from src.visualization.base import ColorPalette, ThemeManager, PlotUtils, BaseVisualization

logger = get_logger("visualization.common")


def create_kda_bar_chart(df: pd.DataFrame, 
                         player_col: str = 'player_name',
                         kills_col: str = 'kills',
                         deaths_col: str = 'deaths',
                         assists_col: str = 'assists',
                         title: Optional[str] = 'KDA by Player',
                         sort_by: Optional[str] = 'kda_ratio',
                         team_col: Optional[str] = None,
                         figsize: Tuple[int, int] = (12, 6)) -> Figure:
    """
    Create a stacked bar chart of KDA (Kills, Deaths, Assists) by player.
    
    Args:
        df: DataFrame containing the data
        player_col: Column name for player identifiers
        kills_col: Column name for kills
        deaths_col: Column name for deaths
        assists_col: Column name for assists
        title: Title for the chart
        sort_by: Column to sort by (default is kda_ratio)
        team_col: Optional column name for team identification
        figsize: Figure size as (width, height)
        
    Returns:
        The generated figure
    """
    # Make a copy to avoid modifying the original dataframe
    plot_df = df.copy()
    
    # Check if we need to calculate KDA ratio
    if sort_by == 'kda_ratio' and 'kda_ratio' not in plot_df.columns:
        plot_df['kda_ratio'] = (plot_df[kills_col] + plot_df[assists_col]) / plot_df[deaths_col].replace(0, 1)
    
    # Sort the dataframe if a sort column is specified
    if sort_by:
        plot_df = plot_df.sort_values(by=sort_by, ascending=False)
    
    # Create figure and axis
    fig, ax = plt.subplots(figsize=figsize)
    
    # Set up bar positions
    players = plot_df[player_col].tolist()
    x = np.arange(len(players))
    width = 0.25
    
    # Plot bars with team coloring if specified
    if team_col:
        bars_kills = []
        bars_deaths = []
        bars_assists = []
        
        for i, (_, player) in enumerate(plot_df.iterrows()):
            team = player[team_col]
            color = ColorPalette.get_team_color(team)
            color_kills = color  # Use team color for kills
            color_deaths = '#e74c3c'  # Always use red for deaths
            color_assists = '#3498db'  # Always use blue for assists
            
            # Plot each bar individually with team color
            bars_kills.append(ax.bar(x[i] - width, player[kills_col], width, color=color_kills, label=f'{team} Kills' if i == 0 else ""))
            bars_deaths.append(ax.bar(x[i], player[deaths_col], width, color=color_deaths, label='Deaths' if i == 0 else ""))
            bars_assists.append(ax.bar(x[i] + width, player[assists_col], width, color=color_assists, label='Assists' if i == 0 else ""))
            
        # Add KDA values as text above each player
        for i, (_, player) in enumerate(plot_df.iterrows()):
            kda = (player[kills_col] + player[assists_col]) / max(player[deaths_col], 1)
            ax.text(x[i], max(player[kills_col], player[deaths_col], player[assists_col]) + 1, 
                   f'KDA: {kda:.2f}', ha='center', va='bottom')
    else:
        # Plot all bars at once if no team coloring
        bars_kills = ax.bar(x - width, plot_df[kills_col], width, color=ColorPalette.get_metric_color('kills'), label='Kills')
        bars_deaths = ax.bar(x, plot_df[deaths_col], width, color=ColorPalette.get_metric_color('deaths'), label='Deaths')
        bars_assists = ax.bar(x + width, plot_df[assists_col], width, color=ColorPalette.get_metric_color('assists'), label='Assists')
        
        # Add KDA values as text above each bar group
        for i, (_, player) in enumerate(plot_df.iterrows()):
            kda = (player[kills_col] + player[assists_col]) / max(player[deaths_col], 1)
            ax.text(x[i], max(player[kills_col], player[deaths_col], player[assists_col]) + 1, 
                   f'KDA: {kda:.2f}', ha='center', va='bottom')
    
    # Add labels, title, and legend
    ax.set_xlabel('Player')
    ax.set_ylabel('Count')
    if title:
        ax.set_title(title)
    ax.set_xticks(x)
    ax.set_xticklabels(players)
    PlotUtils.rotate_xticklabels(ax, rotation=45, ha='right')
    
    # Add legend
    if team_col and len(plot_df[team_col].unique()) > 1:
        # Create custom legend for teams and stats
        team_patches = []
        for team in sorted(plot_df[team_col].unique()):
            team_patches.append(mpatches.Patch(color=ColorPalette.get_team_color(team), label=f'Team {team}'))
        
        stat_patches = [
            mpatches.Patch(color=ColorPalette.get_metric_color('kills'), label='Kills'),
            mpatches.Patch(color=ColorPalette.get_metric_color('deaths'), label='Deaths'),
            mpatches.Patch(color=ColorPalette.get_metric_color('assists'), label='Assists')
        ]
        
        # Create a combined legend with both team and stat information
        ax.legend(handles=team_patches + stat_patches, loc='upper right')
    else:
        ax.legend()
    
    # Add grid
    PlotUtils.add_grid(ax, axis='y', alpha=0.3)
    
    # Adjust layout
    PlotUtils.auto_adjust_figure(fig)
    
    return fig


def create_damage_distribution_chart(df: pd.DataFrame,
                                     player_col: str = 'player_name',
                                     player_damage_col: str = 'player_damage',
                                     objective_damage_col: str = 'objective_damage',
                                     minion_damage_col: str = 'minion_damage',
                                     jungle_damage_col: str = 'jungle_damage',
                                     title: Optional[str] = 'Damage Distribution by Player',
                                     sort_by: Optional[str] = 'player_damage',
                                     team_col: Optional[str] = None,
                                     figsize: Tuple[int, int] = (12, 6)) -> Figure:
    """
    Create a stacked bar chart of damage distribution by player.
    
    Args:
        df: DataFrame containing the data
        player_col: Column name for player identifiers
        player_damage_col: Column name for player damage
        objective_damage_col: Column name for objective damage
        minion_damage_col: Column name for minion damage
        jungle_damage_col: Column name for jungle damage
        title: Title for the chart
        sort_by: Column to sort by
        team_col: Optional column name for team identification
        figsize: Figure size as (width, height)
        
    Returns:
        The generated figure
    """
    # Make a copy to avoid modifying the original dataframe
    plot_df = df.copy()
    
    # Sort the dataframe if a sort column is specified
    if sort_by and sort_by in plot_df.columns:
        plot_df = plot_df.sort_values(by=sort_by, ascending=False)
    
    # Create figure and axis
    fig, ax = plt.subplots(figsize=figsize)
    
    # Set up values
    players = plot_df[player_col].tolist()
    player_damage = plot_df[player_damage_col].tolist()
    objective_damage = plot_df[objective_damage_col].tolist()
    minion_damage = plot_df[minion_damage_col].tolist()
    jungle_damage = plot_df[jungle_damage_col].tolist()
    
    # Calculate totals for percentage labels
    totals = [p + o + m + j for p, o, m, j in zip(
        player_damage, objective_damage, minion_damage, jungle_damage)]
    
    # Set up bar positions
    x = np.arange(len(players))
    width = 0.65
    
    # Adjust team colors if specified
    if team_col:
        # Define colors for each damage type
        colors = {
            'player_damage': [],
            'objective_damage': [],
            'minion_damage': [],
            'jungle_damage': []
        }
        
        # Assign team-specific color variants for each player
        for _, player in plot_df.iterrows():
            team = player[team_col]
            base_color = ColorPalette.get_team_color(team)
            
            # Create different shade variants for different damage types
            colors['player_damage'].append(base_color)
            
            # Derive colors for other damage types from the base color
            rgb = mplcolors.to_rgb(base_color)
            colors['objective_damage'].append(mplcolors.to_hex((rgb[0]*0.8, rgb[1]*0.8, rgb[2]*0.8)))
            colors['minion_damage'].append(mplcolors.to_hex((rgb[0]*0.6, rgb[1]*0.6, rgb[2]*0.6)))
            colors['jungle_damage'].append(mplcolors.to_hex((rgb[0]*0.4, rgb[1]*0.4, rgb[2]*0.4)))
        
        # Plot stacked bars with team colors
        bottom = np.zeros(len(players))
        
        player_bars = ax.bar(x, player_damage, width, bottom=bottom, color=colors['player_damage'], label='Player Damage')
        bottom += player_damage
        
        objective_bars = ax.bar(x, objective_damage, width, bottom=bottom, color=colors['objective_damage'], label='Objective Damage')
        bottom += objective_damage
        
        minion_bars = ax.bar(x, minion_damage, width, bottom=bottom, color=colors['minion_damage'], label='Minion Damage')
        bottom += minion_damage
        
        jungle_bars = ax.bar(x, jungle_damage, width, bottom=bottom, color=colors['jungle_damage'], label='Jungle Damage')
    else:
        # Plot stacked bars with standard colors
        bottom = np.zeros(len(players))
        
        player_bars = ax.bar(x, player_damage, width, bottom=bottom, 
                            color=ColorPalette.get_metric_color('player_damage'), label='Player Damage')
        bottom += player_damage
        
        objective_bars = ax.bar(x, objective_damage, width, bottom=bottom, 
                               color=ColorPalette.get_metric_color('objective_damage'), label='Objective Damage')
        bottom += objective_damage
        
        minion_bars = ax.bar(x, minion_damage, width, bottom=bottom, 
                            color=ColorPalette.ENTITY_COLORS['minion'], label='Minion Damage')
        bottom += minion_damage
        
        jungle_bars = ax.bar(x, jungle_damage, width, bottom=bottom, 
                            color=ColorPalette.ENTITY_COLORS['jungle'], label='Jungle Damage')
    
    # Add labels for percentages
    for i, (player, player_dmg, obj_dmg, minion_dmg, jungle_dmg, total) in enumerate(
            zip(players, player_damage, objective_damage, minion_damage, jungle_damage, totals)):
        # Skip if no damage
        if total == 0:
            continue
            
        # Calculate percentages
        player_pct = player_dmg / total * 100
        obj_pct = obj_dmg / total * 100
        minion_pct = minion_dmg / total * 100
        jungle_pct = jungle_dmg / total * 100
        
        # Only label significant percentages to avoid clutter
        if player_pct > 5:
            ax.text(i, player_dmg/2, f'{player_pct:.0f}%', ha='center', va='center', color='white')
        if obj_pct > 5:
            ax.text(i, player_dmg + obj_dmg/2, f'{obj_pct:.0f}%', ha='center', va='center', color='white')
        if minion_pct > 5:
            ax.text(i, player_dmg + obj_dmg + minion_dmg/2, f'{minion_pct:.0f}%', ha='center', va='center', color='white')
        if jungle_pct > 5:
            ax.text(i, player_dmg + obj_dmg + minion_dmg + jungle_dmg/2, f'{jungle_pct:.0f}%', ha='center', va='center', color='white')
    
    # Add total damage values above each bar
    for i, total in enumerate(totals):
        ax.text(i, total + max(totals) * 0.02, f'{total:,}', ha='center', va='bottom')
    
    # Add labels, title, and legend
    ax.set_xlabel('Player')
    ax.set_ylabel('Damage')
    if title:
        ax.set_title(title)
    ax.set_xticks(x)
    ax.set_xticklabels(players)
    PlotUtils.rotate_xticklabels(ax, rotation=45, ha='right')
    
    # Add legend
    ax.legend(loc='upper right')
    
    # Add grid
    PlotUtils.add_grid(ax, axis='y', alpha=0.3)
    
    # Use thousands separator for y-axis
    PlotUtils.set_thousands_separator(ax, axis='y')
    
    # Adjust layout
    PlotUtils.auto_adjust_figure(fig)
    
    return fig


def create_player_damage_comparison_chart(df: pd.DataFrame,
                                         player_col: str = 'player_name',
                                         damage_col: str = 'player_damage',
                                         dpm_col: Optional[str] = 'damage_per_minute',
                                         title: Optional[str] = 'Player Damage Comparison',
                                         sort_by: Optional[str] = 'player_damage',
                                         team_col: Optional[str] = None,
                                         figsize: Tuple[int, int] = (12, 6)) -> Figure:
    """
    Create a bar chart comparing player damage with optional DPM overlay.
    
    Args:
        df: DataFrame containing the data
        player_col: Column name for player identifiers
        damage_col: Column name for player damage
        dpm_col: Optional column name for damage per minute
        title: Title for the chart
        sort_by: Column to sort by
        team_col: Optional column name for team identification
        figsize: Figure size as (width, height)
        
    Returns:
        The generated figure
    """
    # Make a copy to avoid modifying the original dataframe
    plot_df = df.copy()
    
    # Sort the dataframe if a sort column is specified
    if sort_by and sort_by in plot_df.columns:
        plot_df = plot_df.sort_values(by=sort_by, ascending=False)
    
    # Create figure and axis
    fig, ax1 = plt.subplots(figsize=figsize)
    
    # Set up values
    players = plot_df[player_col].tolist()
    damages = plot_df[damage_col].tolist()
    
    # Set up bar positions
    x = np.arange(len(players))
    width = 0.6
    
    # Plot bars with team coloring if specified
    if team_col:
        # Plot each bar individually with team color
        for i, (_, player) in enumerate(plot_df.iterrows()):
            team = player[team_col]
            color = ColorPalette.get_team_color(team)
            ax1.bar(x[i], player[damage_col], width, color=color, label=f'Team {team}' if i == 0 or plot_df.iloc[i-1][team_col] != team else "")
    else:
        # Plot all bars at once with standard color
        ax1.bar(x, damages, width, color=ColorPalette.get_metric_color('player_damage'), label='Player Damage')
    
    # Add damage values above each bar
    for i, damage in enumerate(damages):
        ax1.text(i, damage + max(damages) * 0.02, f'{damage:,}', ha='center', va='bottom')
    
    # Add damage per minute as a line if available
    if dpm_col and dpm_col in plot_df.columns:
        ax2 = ax1.twinx()
        dpm_values = plot_df[dpm_col].tolist()
        
        line = ax2.plot(x, dpm_values, 'o-', color='red', label='DPM')
        ax2.set_ylabel('Damage Per Minute (DPM)')
        
        # Add DPM values
        for i, dpm in enumerate(dpm_values):
            ax2.text(i, dpm + max(dpm_values) * 0.02, f'{dpm:.1f}', ha='center', va='bottom', color='red')
        
        # Create combined legend
        lines, labels = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax2.legend(lines + lines2, labels + labels2, loc='upper right')
    else:
        # Add normal legend if no DPM
        ax1.legend(loc='upper right')
    
    # Add labels and title
    ax1.set_xlabel('Player')
    ax1.set_ylabel('Total Damage')
    if title:
        ax1.set_title(title)
    ax1.set_xticks(x)
    ax1.set_xticklabels(players)
    PlotUtils.rotate_xticklabels(ax1, rotation=45, ha='right')
    
    # Add grid
    PlotUtils.add_grid(ax1, axis='y', alpha=0.3)
    
    # Use thousands separator for y-axis
    PlotUtils.set_thousands_separator(ax1, axis='y')
    
    # Add average line
    PlotUtils.add_avg_line(ax1, damages, color='gray', label='Avg Damage')
    
    # Adjust layout
    PlotUtils.auto_adjust_figure(fig)
    
    return fig


def create_multimetric_radar_chart(df: pd.DataFrame,
                                  player_col: str = 'player_name',
                                  metrics: List[str] = ['kills', 'deaths', 'assists', 'player_damage', 'healing_done'],
                                  title: Optional[str] = 'Player Performance Radar',
                                  n_players: int = 10,
                                  figsize: Tuple[int, int] = (12, 10)) -> Figure:
    """
    Create a radar chart comparing multiple metrics across players.
    
    Args:
        df: DataFrame containing the data
        player_col: Column name for player identifiers
        metrics: List of metrics to include in the radar chart
        title: Title for the chart
        n_players: Maximum number of players to include
        figsize: Figure size as (width, height)
        
    Returns:
        The generated figure
    """
    # Ensure metrics exist in the dataframe
    available_metrics = [m for m in metrics if m in df.columns]
    
    if not available_metrics:
        raise ValueError("None of the specified metrics are available in the dataframe")
    
    # If we have many players, limit to top N by sum of metrics
    if len(df) > n_players:
        df['metric_sum'] = df[available_metrics].sum(axis=1)
        df = df.sort_values('metric_sum', ascending=False).head(n_players)
    
    # Get player names and normalize metric values for the radar chart
    players = df[player_col].tolist()
    
    # Normalize metrics to 0-1 scale for radar chart
    norm_df = pd.DataFrame()
    
    for metric in available_metrics:
        if metric == 'deaths':  # Deaths are negative, so invert the normalization
            max_val = df[metric].max()
            if max_val > 0:
                norm_df[metric] = 1 - (df[metric] / max_val)
            else:
                norm_df[metric] = 1  # All deaths are 0, so set to 1 (best)
        else:
            max_val = df[metric].max()
            if max_val > 0:
                norm_df[metric] = df[metric] / max_val
            else:
                norm_df[metric] = 0  # All values are 0
    
    # Set up the radar chart
    categories = available_metrics
    N = len(categories)
    
    # Create figure with a grid of radar charts, one per player
    num_players = len(players)
    cols = min(3, num_players)  # Maximum 3 columns
    rows = (num_players + cols - 1) // cols  # Ceiling division for rows
    
    fig = plt.figure(figsize=figsize)
    
    # Set up angles for radar chart
    angles = np.linspace(0, 2*np.pi, N, endpoint=False).tolist()
    angles += angles[:1]  # Close the loop
    
    # Create radar charts
    for i, player in enumerate(players):
        # Create a radar chart for each player
        ax = fig.add_subplot(rows, cols, i+1, polar=True)
        
        # Get player's normalized values
        values = norm_df.iloc[i].tolist()
        values += values[:1]  # Close the loop
        
        # Plot radar
        ax.plot(angles, values, 'o-', linewidth=2, label=player)
        ax.fill(angles, values, alpha=0.25)
        
        # Set category labels
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels([metric.replace('_', ' ').title() for metric in categories])
        
        # Set y limits
        ax.set_ylim(0, 1)
        
        # Set title
        ax.set_title(player, pad=20)
        
        # Remove radial labels
        ax.set_yticklabels([])
    
    # Add an overall title
    if title:
        fig.suptitle(title, fontsize=16, y=0.98)
    
    # Adjust layout
    plt.tight_layout(rect=[0, 0, 1, 0.96])  # Leave space for suptitle
    
    return fig


def create_performance_heatmap(df: pd.DataFrame,
                              player_col: str = 'player_name',
                              metrics: List[str] = ['kills', 'deaths', 'assists', 'player_damage', 'healing_done'],
                              title: Optional[str] = 'Performance Metrics Heatmap',
                              cmap: str = 'viridis',
                              figsize: Tuple[int, int] = (12, 8)) -> Figure:
    """
    Create a heatmap showing multiple performance metrics across players.
    
    Args:
        df: DataFrame containing the data
        player_col: Column name for player identifiers
        metrics: List of metrics to include in the heatmap
        title: Title for the chart
        cmap: Color map to use for the heatmap
        figsize: Figure size as (width, height)
        
    Returns:
        The generated figure
    """
    # Ensure metrics exist in the dataframe
    available_metrics = [m for m in metrics if m in df.columns]
    
    if not available_metrics:
        raise ValueError("None of the specified metrics are available in the dataframe")
    
    # Create pivoted dataframe for heatmap
    plot_df = df[[player_col] + available_metrics].copy()
    
    # Normalize metrics for fair comparison
    norm_df = pd.DataFrame()
    norm_df[player_col] = plot_df[player_col]
    
    for metric in available_metrics:
        if metric == 'deaths':  # Deaths are negative, so invert the normalization
            max_val = plot_df[metric].max()
            if max_val > 0:
                norm_df[metric] = 1 - (plot_df[metric] / max_val)
            else:
                norm_df[metric] = 1  # All deaths are 0, so set to 1 (best)
        else:
            max_val = plot_df[metric].max()
            if max_val > 0:
                norm_df[metric] = plot_df[metric] / max_val
            else:
                norm_df[metric] = 0  # All values are 0
    
    # Create figure
    fig, ax = plt.subplots(figsize=figsize)
    
    # Create heatmap data
    heatmap_data = norm_df.set_index(player_col)
    
    # Rename columns for display
    heatmap_data.columns = [col.replace('_', ' ').title() for col in heatmap_data.columns]
    
    # Create heatmap
    sns.heatmap(heatmap_data, annot=True, cmap=cmap, fmt='.2f', linewidths=.5, ax=ax, cbar_kws={'label': 'Normalized Value'})
    
    # Add labels and title
    ax.set_ylabel('Player')
    if title:
        ax.set_title(title)
    
    # Rotate y-axis labels for better readability
    plt.yticks(rotation=0)
    
    # Adjust layout
    PlotUtils.auto_adjust_figure(fig)
    
    return fig


def create_economy_timeline_chart(df: pd.DataFrame,
                                 time_col: str = 'timestamp',
                                 player_col: str = 'player_name',
                                 gold_col: str = 'gold_earned',
                                 interval: str = '1min',
                                 title: Optional[str] = 'Gold Economy Timeline',
                                 team_col: Optional[str] = None,
                                 figsize: Tuple[int, int] = (14, 8)) -> Figure:
    """
    Create a timeline chart of economy (gold earned) over time.
    
    Args:
        df: DataFrame containing the data
        time_col: Column name for timestamps
        player_col: Column name for player identifiers
        gold_col: Column name for gold values
        interval: Time interval for resampling (e.g., '1min', '30s')
        title: Title for the chart
        team_col: Optional column name for team identification
        figsize: Figure size as (width, height)
        
    Returns:
        The generated figure
    """
    # Check if we have timestamp data
    if time_col not in df.columns or not pd.api.types.is_datetime64_any_dtype(df[time_col]):
        raise ValueError(f"Column {time_col} must be a datetime type")
    
    # Make a copy to avoid modifying the original dataframe
    plot_df = df.copy()
    
    # Ensure the timestamp is set as index for resampling
    if plot_df.index.name != time_col:
        plot_df = plot_df.set_index(time_col)
    
    # Create figure and axis
    fig, ax = plt.subplots(figsize=figsize)
    
    # Track team totals if specified
    if team_col:
        # Group by team and resample
        team_gold = {}
        
        for team in plot_df[team_col].unique():
            team_data = plot_df[plot_df[team_col] == team]
            team_sum = team_data.groupby(player_col)[gold_col].resample(interval).sum().reset_index()
            team_sum['cumulative'] = team_sum.groupby(player_col)[gold_col].cumsum()
            
            # Sum across all players in the team
            team_total = team_sum.groupby(time_col)['cumulative'].sum().reset_index()
            team_gold[team] = team_total
            
            # Plot team total
            color = ColorPalette.get_team_color(team)
            ax.plot(team_total[time_col], team_total['cumulative'], '-', color=color, linewidth=3, label=f'Team {team} Total')
        
        # If we have exactly two teams, plot the gold difference
        if len(team_gold) == 2:
            teams = list(team_gold.keys())
            team1, team2 = teams[0], teams[1]
            
            # Merge team data
            diff_df = pd.merge(team_gold[team1], team_gold[team2], on=time_col, suffixes=('_1', '_2'))
            diff_df['gold_diff'] = diff_df['cumulative_1'] - diff_df['cumulative_2']
            
            # Create a second y-axis for the gold difference
            ax2 = ax.twinx()
            diff_line = ax2.plot(diff_df[time_col], diff_df['gold_diff'], '--', color='black', linewidth=2, label=f'Gold Difference ({team1}-{team2})')
            
            # Set up the second y-axis
            ax2.set_ylabel(f'Gold Difference ({team1}-{team2})')
            ax2.axhline(y=0, color='gray', linestyle='-', alpha=0.3)
            
            # Fill the area above/below zero
            above_zero = diff_df['gold_diff'] > 0
            below_zero = diff_df['gold_diff'] <= 0
            
            if any(above_zero):
                ax2.fill_between(diff_df[time_col].loc[above_zero], 0, diff_df['gold_diff'].loc[above_zero], 
                                color=ColorPalette.get_team_color(team1), alpha=0.2)
            
            if any(below_zero):
                ax2.fill_between(diff_df[time_col].loc[below_zero], 0, diff_df['gold_diff'].loc[below_zero], 
                                color=ColorPalette.get_team_color(team2), alpha=0.2)
    
    # Plot individual player lines
    for player in plot_df.index.get_level_values(player_col).unique():
        player_data = plot_df.loc[plot_df.index.get_level_values(player_col) == player]
        player_resampled = player_data[gold_col].resample(interval).sum().reset_index()
        player_resampled['cumulative'] = player_resampled[gold_col].cumsum()
        
        # Determine line color
        if team_col and team_col in player_data.columns:
            team = player_data[team_col].iloc[0]
            color = ColorPalette.get_team_color(team)
            alpha = 0.6  # Lower alpha for individual players
        else:
            color = next(plt.gca()._get_lines.prop_cycler)['color']
            alpha = 0.8
        
        # Plot the line
        ax.plot(player_resampled[time_col], player_resampled['cumulative'], '-', color=color, alpha=alpha, linewidth=1.5, label=player)
    
    # Add labels, title, and legend
    ax.set_xlabel('Time')
    ax.set_ylabel('Cumulative Gold')
    if title:
        ax.set_title(title)
    
    # Format x-axis to show time in minutes:seconds
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x // 60:.0f}:{x % 60:02.0f}"))
    
    # Add grid
    PlotUtils.add_grid(ax, axis='both', alpha=0.3)
    
    # Use thousands separator for y-axis
    PlotUtils.set_thousands_separator(ax, axis='y')
    
    # Create legend
    if team_col and len(plot_df[team_col].unique()) == 2 and 'ax2' in locals():
        # Get handles and labels from both axes
        handles1, labels1 = ax.get_legend_handles_labels()
        handles2, labels2 = ax2.get_legend_handles_labels()
        
        # Separate team totals and individual players
        team_handles = [h for h, l in zip(handles1, labels1) if 'Team' in l]
        team_labels = [l for l in labels1 if 'Team' in l]
        
        player_handles = [h for h, l in zip(handles1, labels1) if 'Team' not in l]
        player_labels = [l for l in labels1 if 'Team' not in l]
        
        # Create a structured legend
        leg1 = ax.legend(team_handles + handles2, team_labels + labels2, loc='upper left', title='Teams')
        ax.add_artist(leg1)
        
        # Add a second legend for players
        if player_handles:
            ax.legend(player_handles, player_labels, loc='upper right', title='Players')
    else:
        ax.legend(loc='upper left')
    
    # Adjust layout
    PlotUtils.auto_adjust_figure(fig)
    
    return fig 