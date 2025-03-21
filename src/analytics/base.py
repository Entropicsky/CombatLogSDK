"""
Base analyzer module for SMITE 2 CombatLog analytics.

This module provides the BaseAnalyzer abstract class which serves as the foundation
for all analyzer modules in the analytics framework.
"""

import logging
from abc import ABC, abstractmethod
from copy import deepcopy
from typing import Any, Dict, Optional, List, Callable, TypeVar, Generic, Union, Tuple

import pandas as pd

from ..parser import CombatLogParser

logger = logging.getLogger(__name__)

T = TypeVar('T')

class BaseAnalyzer(ABC):
    """
    Abstract base class for SMITE 2 CombatLog analyzers.
    
    This class provides the common structure and functionality for all analyzer modules
    in the analytics framework. Each specialized analyzer should inherit from this class
    and implement the required abstract methods.
    
    Attributes:
        parser (CombatLogParser): The parser instance containing the parsed data
        config (Dict[str, Any]): Configuration parameters for the analyzer
        _cached_results (Dict[str, Any]): Cache for storing computed results
    """
    
    def __init__(self, parser: CombatLogParser, **config):
        """
        Initialize the BaseAnalyzer.
        
        Args:
            parser: The CombatLogParser instance containing the parsed data
            **config: Optional configuration parameters for the analyzer
        """
        self.parser = parser
        self.config = self._merge_config(config)
        self._validate_parser()
        self._cached_results = {}
    
    @abstractmethod
    def _default_config(self) -> Dict[str, Any]:
        """
        Return the default configuration for the analyzer.
        
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
    
    def _validate_parser(self) -> None:
        """
        Validate that the parser contains the required data for the analyzer.
        
        This method checks that the parser has been initialized with data.
        Subclasses may override this method to add additional validation.
        
        Raises:
            ValueError: If the parser does not contain valid data
        """
        if not hasattr(self.parser, 'events') or not self.parser.events:
            raise ValueError("Parser does not contain any events. Please call parser.parse() first.")
    
    def _get_cached_or_calculate(self, key: str, calculation_func: Callable[[], T]) -> T:
        """
        Get a result from cache or calculate and cache it.
        
        This method serves as a caching mechanism for expensive calculations.
        
        Args:
            key: The cache key for the result
            calculation_func: A function that calculates the result if not cached
            
        Returns:
            The cached or newly calculated result
        """
        if key not in self._cached_results:
            logger.debug(f"Cache miss for {key}, calculating...")
            self._cached_results[key] = calculation_func()
        return self._cached_results[key]
    
    def clear_cache(self) -> None:
        """
        Clear the cached results.
        
        This method removes all cached calculations, forcing recalculation
        on the next request.
        """
        self._cached_results = {}
        logger.debug("Cache cleared")
    
    def reset_config(self) -> None:
        """
        Reset the configuration to default values.
        
        This method resets all configuration parameters to their default values
        and clears the cache.
        """
        self.config = self._default_config()
        self.clear_cache()
        logger.debug("Configuration reset to defaults")
    
    def update_config(self, **config) -> None:
        """
        Update the configuration parameters.
        
        This method updates the configuration with new parameters and clears
        the cache to ensure consistency.
        
        Args:
            **config: New configuration parameters
        """
        self.config.update(config)
        self.clear_cache()
        logger.debug("Configuration updated")
    
    @abstractmethod
    def analyze(self) -> Dict[str, Any]:
        """
        Perform the main analysis and return results.
        
        This is the primary method that should be implemented by subclasses to
        perform their specialized analysis.
        
        Returns:
            Dict[str, Any]: The analysis results
        """
        pass
    
    def to_dataframe(self) -> pd.DataFrame:
        """
        Convert the analysis results to a DataFrame.
        
        This method should be implemented by subclasses to provide a DataFrame
        representation of the analysis results for easier manipulation.
        
        Returns:
            pd.DataFrame: The analysis results as a DataFrame
        """
        results = self.analyze()
        return pd.DataFrame([results])
    
    def export_results(self, file_path: str, format: str = 'csv') -> None:
        """
        Export the analysis results to a file.
        
        Args:
            file_path: The path where the file will be saved
            format: The file format ('csv', 'json', 'xlsx')
            
        Raises:
            ValueError: If the format is not supported
        """
        df = self.to_dataframe()
        
        if format.lower() == 'csv':
            df.to_csv(file_path, index=False)
        elif format.lower() == 'json':
            df.to_json(file_path, orient='records')
        elif format.lower() == 'xlsx':
            df.to_excel(file_path, index=False)
        else:
            raise ValueError(f"Unsupported export format: {format}. Use 'csv', 'json', or 'xlsx'.")
        
        logger.info(f"Analysis results exported to {file_path} in {format} format") 