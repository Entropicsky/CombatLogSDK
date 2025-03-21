"""
Enhanced logging utility for SMITE 2 CombatLog Parser.

This module provides advanced logging capabilities including hierarchical loggers,
custom formatting, and both file and console output.
"""

import logging
import os
import sys
from datetime import datetime
from typing import Optional, Dict, Any, List


class LogManager:
    """
    Manager for application logging.
    
    This class provides a centralized way to manage logging configuration
    and create module-specific loggers with consistent settings.
    """
    
    _instance = None
    _loggers = {}
    
    def __new__(cls):
        """Create a singleton instance of LogManager."""
        if cls._instance is None:
            cls._instance = super(LogManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the LogManager."""
        if self._initialized:
            return
            
        self.log_dir = "logs"
        self.default_level = logging.INFO
        self.formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
        )
        
        # Create log directory if it doesn't exist
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Set up the root logger
        self._setup_root_logger()
        
        self._initialized = True
    
    def _setup_root_logger(self):
        """Configure the root logger with basic settings."""
        root_logger = logging.getLogger()
        root_logger.setLevel(self.default_level)
        
        # Clear existing handlers to avoid duplicates
        if root_logger.handlers:
            root_logger.handlers.clear()
        
        # Add a console handler with WARNING level
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.WARNING)
        console_handler.setFormatter(self.formatter)
        root_logger.addHandler(console_handler)
    
    def get_logger(self, module_name: str, level: Optional[int] = None) -> logging.Logger:
        """
        Get a logger for a specific module.
        
        Args:
            module_name: The name of the module (e.g., 'analytics.performance')
            level: Optional logging level (defaults to the manager's default level)
            
        Returns:
            A configured logger for the module
        """
        if module_name in self._loggers:
            return self._loggers[module_name]
        
        logger = logging.getLogger(module_name)
        level = level or self.default_level
        logger.setLevel(level)
        
        # Create a timestamped log file for this module
        timestamp = datetime.now().strftime("%Y%m%d")
        log_file = f"{self.log_dir}/{module_name.replace('.', '_')}_{timestamp}.log"
        
        # Add a file handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(self.formatter)
        logger.addHandler(file_handler)
        
        # Store the logger
        self._loggers[module_name] = logger
        
        return logger
    
    def set_level(self, level: int, module_name: Optional[str] = None):
        """
        Set the logging level for a specific module or all loggers.
        
        Args:
            level: The logging level (e.g., logging.DEBUG)
            module_name: Optional module name (if None, sets level for all loggers)
        """
        if module_name is None:
            # Set level for all loggers
            self.default_level = level
            for name, logger in self._loggers.items():
                logger.setLevel(level)
                for handler in logger.handlers:
                    if isinstance(handler, logging.FileHandler):
                        handler.setLevel(level)
        elif module_name in self._loggers:
            # Set level for specific logger
            logger = self._loggers[module_name]
            logger.setLevel(level)
            for handler in logger.handlers:
                if isinstance(handler, logging.FileHandler):
                    handler.setLevel(level)


# Create a convenience function for getting loggers
def get_logger(module_name: str, level: Optional[int] = None) -> logging.Logger:
    """
    Get a configured logger for a module.
    
    This is a convenience function that uses the LogManager singleton.
    
    Args:
        module_name: The name of the module
        level: Optional logging level
        
    Returns:
        A configured logger
    """
    manager = LogManager()
    return manager.get_logger(module_name, level)


def set_log_level(level: int, module_name: Optional[str] = None):
    """
    Set logging level for all or specific modules.
    
    Args:
        level: The logging level
        module_name: Optional module name to set level for
    """
    manager = LogManager()
    manager.set_level(level, module_name)


class LogContext:
    """
    Context manager for grouped log messages.
    
    This class provides a way to group related log messages together
    with additional context information.
    """
    
    def __init__(self, logger: logging.Logger, context: str, extra: Optional[Dict[str, Any]] = None):
        """
        Initialize a logging context.
        
        Args:
            logger: The logger to use
            context: A description of the context
            extra: Optional extra information to include in log messages
        """
        self.logger = logger
        self.context = context
        self.extra = extra or {}
    
    def __enter__(self):
        """Enter the context and log the start."""
        self.logger.info(f"=== START: {self.context} ===")
        if self.extra:
            self.logger.info(f"Context: {self.extra}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context and log the end."""
        if exc_type:
            self.logger.error(f"=== ERROR: {self.context} - {exc_val} ===", exc_info=True)
        else:
            self.logger.info(f"=== END: {self.context} ===")
        return False  # Don't suppress exceptions


def log_method_calls(logger: logging.Logger, level: int = logging.DEBUG):
    """
    Decorator to log method calls with arguments and return values.
    
    Args:
        logger: The logger to use
        level: The logging level for the messages
        
    Returns:
        A decorator function
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Log method call with arguments
            args_repr = [repr(a) for a in args[1:]] if len(args) > 0 and hasattr(args[0], '__class__') else [repr(a) for a in args]
            kwargs_repr = [f"{k}={repr(v)}" for k, v in kwargs.items()]
            signature = ", ".join(args_repr + kwargs_repr)
            logger.log(level, f"Calling {func.__name__}({signature})")
            
            # Call the function
            result = func(*args, **kwargs)
            
            # Log the result
            logger.log(level, f"{func.__name__} returned {repr(result)}")
            
            return result
        return wrapper
    return decorator 