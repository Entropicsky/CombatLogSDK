"""
Base visualization module for SMITE 2 CombatLog visualizations.

This module provides the BaseVisualization abstract class which serves as the
foundation for all visualization classes in the framework.
"""

import os
from abc import ABC, abstractmethod
from copy import deepcopy
from typing import Any, Dict, List, Optional, Tuple, Union, cast

import matplotlib.pyplot as plt
import matplotlib.colors as mplcolors
from matplotlib.figure import Figure
import matplotlib as mpl
import numpy as np
import pandas as pd
from matplotlib.transforms import Bbox

from src.utils.logging import get_logger

logger = get_logger("visualization.base")


class BaseVisualization(ABC):
    """
    Abstract base class for all visualizations.
    
    This class provides common functionality for generating and exporting
    visualizations based on analytics results.
    
    Attributes:
        analyzer: The analyzer instance containing the data
        config: Configuration parameters for the visualization
        figure: The matplotlib figure (None until generate is called)
    """
    
    def __init__(self, analyzer: Any, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the visualization.
        
        Args:
            analyzer: The analyzer containing the data to visualize
            config: Optional configuration parameters
        """
        self.analyzer = analyzer
        self.config = self._merge_config(config or {})
        self.figure: Optional[Figure] = None
        
    @abstractmethod
    def _default_config(self) -> Dict[str, Any]:
        """
        Return the default configuration for the visualization.
        
        This method should be implemented by subclasses to provide
        default values for configuration parameters.
        
        Returns:
            Dict[str, Any]: Default configuration parameters
        """
        pass
    
    def _merge_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge the provided configuration with the default configuration.
        
        Args:
            config: The configuration parameters provided during initialization
            
        Returns:
            Dict[str, Any]: The merged configuration dictionary
        """
        default_config = self._default_config()
        merged_config = deepcopy(default_config)
        merged_config.update(config)
        return merged_config
    
    @abstractmethod
    def generate(self) -> Figure:
        """
        Generate the visualization.
        
        This method should be implemented by subclasses to create the
        visualization based on the analyzer data and configuration.
        
        Returns:
            matplotlib.figure.Figure: The generated figure
        """
        pass
    
    def export(self, path: str, format: str = 'png', dpi: int = 300, **kwargs) -> str:
        """
        Export the visualization to a file.
        
        Args:
            path: The path where the file will be saved
            format: The file format (png, jpg, svg, pdf)
            dpi: The resolution for raster formats
            **kwargs: Additional arguments for plt.savefig
            
        Returns:
            str: The full path to the saved file
            
        Raises:
            ValueError: If format is not supported
            RuntimeError: If the figure hasn't been generated
        """
        if self.figure is None:
            try:
                self.figure = self.generate()
            except Exception as e:
                raise RuntimeError(f"Failed to generate figure: {str(e)}")
        
        # Create directory if it doesn't exist
        directory = os.path.dirname(path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
        
        # Add extension if not present
        if not path.lower().endswith(f'.{format.lower()}'):
            path = f"{path}.{format.lower()}"
        
        # Save the figure
        self.figure.savefig(path, format=format, dpi=dpi, **kwargs)
        logger.info(f"Exported visualization to {path}")
        
        return path
    
    def display(self) -> None:
        """
        Display the visualization.
        
        This method displays the visualization using matplotlib's show function.
        If the figure hasn't been generated yet, it calls generate first.
        """
        if self.figure is None:
            self.figure = self.generate()
            
        plt.show()
    
    def close(self) -> None:
        """
        Close the figure to free memory.
        """
        if self.figure is not None:
            plt.close(self.figure)
            self.figure = None
            
        
class ColorPalette:
    """
    Color palette for consistent visualization styling.
    
    This class provides a set of color palettes for use in visualizations.
    """
    
    # Default color palettes
    DEFAULT = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
               '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
    
    TEAM_COLORS = {
        'order': '#3498db',  # Blue
        'chaos': '#e74c3c',  # Red
    }
    
    ENTITY_COLORS = {
        'player': '#3498db',      # Blue
        'minion': '#27ae60',      # Green
        'jungle': '#8e44ad',      # Purple
        'objective': '#f39c12',   # Orange
        'tower': '#e74c3c',       # Red
        'phoenix': '#d35400',     # Dark Orange
        'titan': '#c0392b',       # Dark Red
        'other': '#7f8c8d',       # Gray
    }
    
    ROLE_COLORS = {
        'solo': '#3498db',        # Blue
        'jungle': '#8e44ad',      # Purple
        'mid': '#f39c12',         # Orange
        'support': '#27ae60',     # Green
        'carry': '#e74c3c',       # Red
        'unknown': '#7f8c8d',     # Gray
    }
    
    METRIC_COLORS = {
        'kills': '#27ae60',       # Green
        'deaths': '#e74c3c',      # Red
        'assists': '#3498db',     # Blue
        'player_damage': '#8e44ad',  # Purple
        'objective_damage': '#f39c12',  # Orange
        'healing': '#1abc9c',     # Turquoise
        'gold': '#f1c40f',        # Yellow
        'experience': '#2ecc71',  # Emerald
    }
    
    @classmethod
    def get_team_color(cls, team: str) -> str:
        """
        Get the color for a team.
        
        Args:
            team: The team name (order or chaos)
            
        Returns:
            The color for the team
        """
        team = team.lower()
        return cls.TEAM_COLORS.get(team, cls.TEAM_COLORS['order'])
    
    @classmethod
    def get_entity_color(cls, entity_type: str) -> str:
        """
        Get the color for an entity type.
        
        Args:
            entity_type: The entity type
            
        Returns:
            The color for the entity type
        """
        entity_type = entity_type.lower()
        return cls.ENTITY_COLORS.get(entity_type, cls.ENTITY_COLORS['other'])
    
    @classmethod
    def get_role_color(cls, role: str) -> str:
        """
        Get the color for a role.
        
        Args:
            role: The role name
            
        Returns:
            The color for the role
        """
        role = role.lower()
        return cls.ROLE_COLORS.get(role, cls.ROLE_COLORS['unknown'])
    
    @classmethod
    def get_metric_color(cls, metric: str) -> str:
        """
        Get the color for a metric.
        
        Args:
            metric: The metric name
            
        Returns:
            The color for the metric
        """
        metric = metric.lower()
        return cls.METRIC_COLORS.get(metric, cls.DEFAULT[0])
    
    @classmethod
    def get_sequential_palette(cls, n: int = 10) -> List[str]:
        """
        Get a sequential color palette with the specified number of colors.
        
        Args:
            n: The number of colors
            
        Returns:
            A list of colors
        """
        cmap = plt.cm.get_cmap('viridis', n)
        return [mplcolors.rgb2hex(cmap(i)) for i in range(n)]
    
    @classmethod
    def get_diverging_palette(cls, n: int = 10) -> List[str]:
        """
        Get a diverging color palette with the specified number of colors.
        
        Args:
            n: The number of colors
            
        Returns:
            A list of colors
        """
        cmap = plt.cm.get_cmap('RdBu_r', n)
        return [mplcolors.rgb2hex(cmap(i)) for i in range(n)]


class ThemeManager:
    """
    Manager for visualization themes.
    
    This class provides methods for setting and applying themes to matplotlib
    visualizations.
    """
    
    # Predefined themes
    THEMES = {
        'default': {
            'figure.figsize': (10, 6),
            'figure.facecolor': 'white',
            'axes.facecolor': 'white',
            'axes.grid': True,
            'grid.alpha': 0.3,
            'axes.spines.top': False,
            'axes.spines.right': False,
            'font.family': 'sans-serif',
            'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans'],
            'font.size': 10,
            'axes.labelsize': 12,
            'xtick.labelsize': 10,
            'ytick.labelsize': 10,
            'legend.fontsize': 10,
            'lines.linewidth': 2,
            'patch.linewidth': 0.5,
            'xtick.major.pad': 7,
            'ytick.major.pad': 7,
            'xtick.minor.visible': False,
            'ytick.minor.visible': False,
        },
        'dark': {
            'figure.figsize': (10, 6),
            'figure.facecolor': '#222222',
            'axes.facecolor': '#222222',
            'axes.edgecolor': '#aaaaaa',
            'axes.labelcolor': '#ffffff',
            'axes.grid': True,
            'grid.alpha': 0.3,
            'axes.spines.top': False,
            'axes.spines.right': False,
            'text.color': '#ffffff',
            'xtick.color': '#ffffff',
            'ytick.color': '#ffffff',
            'grid.color': '#555555',
            'font.family': 'sans-serif',
            'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans'],
            'font.size': 10,
            'axes.labelsize': 12,
            'xtick.labelsize': 10,
            'ytick.labelsize': 10,
            'legend.fontsize': 10,
            'legend.facecolor': '#333333',
            'legend.edgecolor': '#aaaaaa',
            'lines.linewidth': 2,
            'patch.linewidth': 0.5,
            'xtick.major.pad': 7,
            'ytick.major.pad': 7,
            'xtick.minor.visible': False,
            'ytick.minor.visible': False,
        },
        'minimal': {
            'figure.figsize': (10, 6),
            'figure.facecolor': 'white',
            'axes.facecolor': 'white',
            'axes.grid': False,
            'axes.spines.top': False,
            'axes.spines.right': False,
            'axes.spines.bottom': True,
            'axes.spines.left': True,
            'font.family': 'sans-serif',
            'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans'],
            'font.size': 10,
            'axes.labelsize': 12,
            'xtick.labelsize': 10,
            'ytick.labelsize': 10,
            'legend.fontsize': 10,
            'lines.linewidth': 2,
            'patch.linewidth': 0.5,
            'xtick.major.pad': 7,
            'ytick.major.pad': 7,
            'xtick.minor.visible': False,
            'ytick.minor.visible': False,
        },
    }
    
    @classmethod
    def apply_theme(cls, theme: Union[str, Dict[str, Any]] = 'default') -> None:
        """
        Apply a theme to matplotlib.
        
        Args:
            theme: The name of a predefined theme or a dictionary of parameters
            
        Raises:
            ValueError: If the theme name is not found
        """
        if isinstance(theme, str):
            if theme not in cls.THEMES:
                raise ValueError(f"Theme '{theme}' not found")
            theme_params = cls.THEMES[theme]
        else:
            theme_params = theme
            
        # Apply the theme parameters
        for param, value in theme_params.items():
            try:
                plt.rcParams[param] = value
            except KeyError:
                logger.warning(f"Invalid matplotlib parameter: {param} - skipping")
            except Exception as e:
                logger.warning(f"Error setting {param}={value}: {str(e)}")
            
        logger.debug(f"Applied theme: {theme if isinstance(theme, str) else 'custom'}")
    
    @classmethod
    def reset_theme(cls) -> None:
        """
        Reset matplotlib parameters to defaults.
        """
        plt.rcdefaults()
        logger.debug("Reset matplotlib theme to defaults")
    
    @classmethod
    def register_theme(cls, name: str, params: Dict[str, Any]) -> None:
        """
        Register a new theme.
        
        Args:
            name: The name of the theme
            params: The theme parameters
            
        Raises:
            ValueError: If a theme with the name already exists
        """
        if name in cls.THEMES:
            raise ValueError(f"Theme '{name}' already exists")
            
        cls.THEMES[name] = params
        logger.debug(f"Registered new theme: {name}")


class PlotUtils:
    """
    Utility functions for plot creation and formatting.
    
    This class provides helper methods for common plot formatting tasks.
    """
    
    @staticmethod
    def format_axis_labels(ax: plt.Axes, x_label: Optional[str] = None, 
                           y_label: Optional[str] = None, title: Optional[str] = None) -> None:
        """
        Format the axis labels and title.
        
        Args:
            ax: The axes to format
            x_label: Optional x-axis label
            y_label: Optional y-axis label
            title: Optional title
        """
        if x_label:
            ax.set_xlabel(x_label)
        if y_label:
            ax.set_ylabel(y_label)
        if title:
            ax.set_title(title)
    
    @staticmethod
    def format_legend(ax: plt.Axes, loc: str = 'best', frameon: bool = True, 
                      fontsize: Optional[int] = None) -> None:
        """
        Format the legend.
        
        Args:
            ax: The axes to format
            loc: Legend location
            frameon: Whether to draw a frame around the legend
            fontsize: Font size for legend text
        """
        ax.legend(loc=loc, frameon=frameon, fontsize=fontsize)
    
    @staticmethod
    def add_grid(ax: plt.Axes, axis: str = 'both', alpha: float = 0.3) -> None:
        """
        Add a grid to the plot.
        
        Args:
            ax: The axes to format
            axis: Which axis to add grid lines to ('x', 'y', or 'both')
            alpha: Transparency of grid lines
        """
        ax.grid(axis=axis, alpha=alpha)
    
    @staticmethod
    def add_value_labels(ax: plt.Axes, fontsize: int = 9, 
                         fmt: str = '{:.1f}', spacing: int = 5) -> None:
        """
        Add value labels to bar plots.
        
        Args:
            ax: The axes containing the bar plot
            fontsize: Font size for labels
            fmt: Format string for values
            spacing: Vertical spacing in points
        """
        for rect in ax.patches:
            height = rect.get_height()
            width = rect.get_width()
            x = rect.get_x() + width / 2
            y = rect.get_y() + height
            
            label = fmt.format(height)
            
            ax.annotate(
                label,
                (x, y),
                xytext=(0, spacing),
                textcoords="offset points",
                ha='center',
                va='bottom',
                fontsize=fontsize
            )
    
    @staticmethod
    def add_avg_line(ax: plt.Axes, data: Union[List[float], np.ndarray], 
                     color: str = 'red', linestyle: str = '--', 
                     label: Optional[str] = 'Average', alpha: float = 0.7) -> None:
        """
        Add an average line to a plot.
        
        Args:
            ax: The axes to add the line to
            data: The data to calculate the average from
            color: Line color
            linestyle: Line style
            label: Line label
            alpha: Line transparency
        """
        avg = np.mean(data)
        ax.axhline(y=avg, color=color, linestyle=linestyle, alpha=alpha, label=label)
        
        # Add text annotation with the average value
        ax.annotate(
            f'Avg: {avg:.2f}',
            xy=(0.02, avg),
            xycoords=('axes fraction', 'data'),
            textcoords='offset points',
            xytext=(0, 5),
            ha='left',
            va='bottom',
            color=color,
            alpha=alpha
        )
    
    @staticmethod
    def set_thousands_separator(ax: plt.Axes, axis: str = 'both') -> None:
        """
        Set thousand separators for axis tick labels.
        
        Args:
            ax: The axes to format
            axis: Which axis to format ('x', 'y', or 'both')
        """
        from matplotlib.ticker import FuncFormatter
        
        def thousands_formatter(x, pos):
            return f'{int(x):,}'
        
        formatter = FuncFormatter(thousands_formatter)
        
        if axis in ('x', 'both'):
            ax.xaxis.set_major_formatter(formatter)
        if axis in ('y', 'both'):
            ax.yaxis.set_major_formatter(formatter)
    
    @staticmethod
    def rotate_xticklabels(ax: plt.Axes, rotation: float = 45, ha: str = 'right') -> None:
        """
        Rotate x-axis tick labels.
        
        Args:
            ax: The axes to format
            rotation: Rotation angle in degrees
            ha: Horizontal alignment
        """
        for label in ax.get_xticklabels():
            label.set_rotation(rotation)
            label.set_ha(ha)
    
    @staticmethod
    def auto_adjust_figure(fig: Figure) -> None:
        """
        Automatically adjust the figure layout.
        
        Args:
            fig: The figure to adjust
        """
        fig.tight_layout()
    
    @staticmethod
    def add_watermark(fig: Figure, text: str = 'SMITE 2 CombatLog Parser', 
                      alpha: float = 0.1, fontsize: int = 40, color: str = 'gray') -> None:
        """
        Add a watermark to the figure.
        
        Args:
            fig: The figure to add the watermark to
            text: The watermark text
            alpha: Transparency of the watermark
            fontsize: Font size of the watermark
            color: Color of the watermark
        """
        fig.text(0.5, 0.5, text, ha='center', va='center', alpha=alpha,
                fontsize=fontsize, color=color, transform=fig.transFigure,
                rotation=30, fontweight='bold') 