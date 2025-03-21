"""
Performance profiling utilities for SMITE 2 CombatLog Parser.

This module provides tools for monitoring and optimizing the performance
of the parser and analyzer components.
"""

import functools
import time
import tracemalloc
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar, Union
import logging

from src.utils.logging import get_logger

logger = get_logger("utils.profiling")

T = TypeVar('T')


def profile_time(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to profile the execution time of a function.
    
    Args:
        func: The function to profile
        
    Returns:
        A wrapped function that logs execution time
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # Get function context for better logging
        if args and hasattr(args[0], '__class__'):
            class_name = args[0].__class__.__name__
            func_name = f"{class_name}.{func.__name__}"
        else:
            func_name = func.__name__
            
        logger.debug(f"Function {func_name} took {execution_time:.4f} seconds to execute")
        
        return result
    return wrapper


def profile_memory(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to profile the memory usage of a function.
    
    Args:
        func: The function to profile
        
    Returns:
        A wrapped function that logs memory usage
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        tracemalloc.start()
        
        result = func(*args, **kwargs)
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # Get function context for better logging
        if args and hasattr(args[0], '__class__'):
            class_name = args[0].__class__.__name__
            func_name = f"{class_name}.{func.__name__}"
        else:
            func_name = func.__name__
        
        current_mb = current / 1024 / 1024
        peak_mb = peak / 1024 / 1024
        
        logger.debug(f"Function {func_name} memory usage: current={current_mb:.2f}MB, peak={peak_mb:.2f}MB")
        
        return result
    return wrapper


class Profiler:
    """
    Class for detailed profiling of code blocks.
    
    This class provides methods for measuring and reporting the performance
    of specific code blocks.
    """
    
    def __init__(self, name: str = "default"):
        """
        Initialize a profiler.
        
        Args:
            name: A name for this profiler instance
        """
        self.name = name
        self.timers = {}
        self.memory_usage = {}
        self.logger = get_logger(f"utils.profiling.{name}")
        
    def start_timer(self, label: str):
        """
        Start a timer with the given label.
        
        Args:
            label: A label for this timing operation
        """
        self.timers[label] = {"start": time.time(), "end": None}
        self.logger.debug(f"Timer '{label}' started")
        
    def stop_timer(self, label: str) -> float:
        """
        Stop a timer and return the elapsed time.
        
        Args:
            label: The label of the timer to stop
            
        Returns:
            The elapsed time in seconds
            
        Raises:
            ValueError: If the timer was not started
        """
        if label not in self.timers or self.timers[label]["start"] is None:
            raise ValueError(f"Timer '{label}' was not started")
            
        if self.timers[label]["end"] is not None:
            self.logger.warning(f"Timer '{label}' was already stopped")
            return self.get_elapsed_time(label)
            
        self.timers[label]["end"] = time.time()
        elapsed = self.get_elapsed_time(label)
        
        self.logger.debug(f"Timer '{label}' stopped after {elapsed:.4f} seconds")
        return elapsed
        
    def get_elapsed_time(self, label: str) -> float:
        """
        Get the elapsed time for a timer.
        
        Args:
            label: The label of the timer
            
        Returns:
            The elapsed time in seconds
            
        Raises:
            ValueError: If the timer was not started
        """
        if label not in self.timers:
            raise ValueError(f"Timer '{label}' does not exist")
            
        timer = self.timers[label]
        
        if timer["start"] is None:
            raise ValueError(f"Timer '{label}' was not started")
            
        if timer["end"] is None:
            # Timer is still running, return current elapsed time
            return time.time() - timer["start"]
            
        return timer["end"] - timer["start"]
    
    def start_memory_tracking(self, label: str):
        """
        Start tracking memory usage for a code block.
        
        Args:
            label: A label for this memory tracking operation
        """
        tracemalloc.start()
        self.memory_usage[label] = {"start": None, "current": None, "peak": None}
        self.memory_usage[label]["start"] = tracemalloc.get_traced_memory()[0]
        self.logger.debug(f"Memory tracking '{label}' started")
        
    def stop_memory_tracking(self, label: str) -> Tuple[float, float]:
        """
        Stop tracking memory usage and return the results.
        
        Args:
            label: The label of the memory tracking operation
            
        Returns:
            A tuple of (current memory usage, peak memory usage) in MB
            
        Raises:
            ValueError: If memory tracking was not started for this label
        """
        if label not in self.memory_usage:
            raise ValueError(f"Memory tracking '{label}' was not started")
            
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        self.memory_usage[label]["current"] = current
        self.memory_usage[label]["peak"] = peak
        
        current_mb = (current - self.memory_usage[label]["start"]) / 1024 / 1024
        peak_mb = peak / 1024 / 1024
        
        self.logger.debug(f"Memory tracking '{label}' stopped: allocated={current_mb:.2f}MB, peak={peak_mb:.2f}MB")
        
        return current_mb, peak_mb
    
    def report(self):
        """
        Generate and log a full profiling report.
        
        This method logs all timers and memory tracking results.
        """
        self.logger.info(f"=== Profiling Report: {self.name} ===")
        
        if self.timers:
            self.logger.info("Timing Results:")
            for label, timer in sorted(self.timers.items()):
                try:
                    elapsed = self.get_elapsed_time(label)
                    status = "running" if timer["end"] is None else "completed"
                    self.logger.info(f"  {label}: {elapsed:.4f}s ({status})")
                except ValueError as e:
                    self.logger.warning(f"  {label}: {str(e)}")
        
        if self.memory_usage:
            self.logger.info("Memory Usage:")
            for label, usage in sorted(self.memory_usage.items()):
                if usage["current"] is not None:
                    current_mb = (usage["current"] - usage["start"]) / 1024 / 1024
                    peak_mb = usage["peak"] / 1024 / 1024
                    self.logger.info(f"  {label}: allocated={current_mb:.2f}MB, peak={peak_mb:.2f}MB")
                else:
                    self.logger.warning(f"  {label}: tracking not completed")
        
        self.logger.info(f"=== End of Profiling Report: {self.name} ===")


class TimingContext:
    """
    Context manager for timing code blocks.
    
    This class provides a convenient way to time code blocks using a context manager.
    """
    
    def __init__(self, label: str, logger: Optional[logging.Logger] = None, level: int = logging.DEBUG):
        """
        Initialize a timing context.
        
        Args:
            label: A label for this timing operation
            logger: Optional logger (defaults to the profiling module logger)
            level: Logging level for the timing messages
        """
        self.label = label
        self.logger = logger or get_logger("utils.profiling")
        self.level = level
        self.start_time = None
        
    def __enter__(self):
        """Start the timer."""
        self.start_time = time.time()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Stop the timer and log the elapsed time.
        
        If an exception occurred, it will be noted in the log.
        """
        end_time = time.time()
        elapsed = end_time - self.start_time
        
        if exc_type:
            self.logger.log(self.level, f"Code block '{self.label}' raised {exc_type.__name__}: {elapsed:.4f}s")
        else:
            self.logger.log(self.level, f"Code block '{self.label}' completed in {elapsed:.4f}s")
            
        return False  # Don't suppress exceptions 