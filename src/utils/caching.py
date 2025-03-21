"""
Caching utilities for SMITE 2 CombatLog Parser.

This module provides tools for caching expensive computation results
to improve performance in the analytics modules.
"""

import os
import pickle
import hashlib
import json
import functools
import time
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar, Union, cast
import logging

from src.utils.logging import get_logger

logger = get_logger("utils.caching")

T = TypeVar('T')


class DiskCache:
    """
    Disk-based cache for storing computation results.
    
    This class provides a way to cache expensive computation results to disk,
    allowing them to be reused across multiple runs.
    """
    
    def __init__(self, cache_dir: str = ".cache", ttl: Optional[int] = None):
        """
        Initialize the disk cache.
        
        Args:
            cache_dir: Directory to store cache files
            ttl: Optional time-to-live in seconds for cache entries
        """
        self.cache_dir = cache_dir
        self.ttl = ttl
        
        # Create cache directory if it doesn't exist
        os.makedirs(cache_dir, exist_ok=True)
        
        logger.debug(f"Initialized disk cache in directory: {cache_dir}")
    
    def _get_cache_path(self, key: str) -> str:
        """
        Get the file path for a cache key.
        
        Args:
            key: The cache key
            
        Returns:
            The file path for the cache entry
        """
        return os.path.join(self.cache_dir, f"{key}.pickle")
    
    def _get_cache_key(self, func_name: str, args: tuple, kwargs: Dict[str, Any]) -> str:
        """
        Generate a cache key for a function call.
        
        Args:
            func_name: The name of the function
            args: Positional arguments to the function
            kwargs: Keyword arguments to the function
            
        Returns:
            A hash-based cache key
        """
        # Create a string representation of the function call
        args_str = str(args)
        kwargs_str = str(sorted(kwargs.items()))
        call_str = f"{func_name}:{args_str}:{kwargs_str}"
        
        # Generate a hash of the call string
        hash_obj = hashlib.md5(call_str.encode('utf-8'))
        return hash_obj.hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.
        
        Args:
            key: The cache key
            
        Returns:
            The cached value, or None if not found or expired
        """
        cache_path = self._get_cache_path(key)
        
        if not os.path.exists(cache_path):
            logger.debug(f"Cache miss for key: {key}")
            return None
        
        try:
            with open(cache_path, 'rb') as f:
                cache_entry = pickle.load(f)
                
            # Check if the entry has expired
            if self.ttl is not None:
                timestamp = cache_entry.get('timestamp')
                if timestamp is None or (time.time() - timestamp) > self.ttl:
                    logger.debug(f"Cache entry expired for key: {key}")
                    return None
                    
            logger.debug(f"Cache hit for key: {key}")
            return cache_entry.get('value')
            
        except (pickle.PickleError, IOError, EOFError) as e:
            logger.warning(f"Error reading cache entry for key {key}: {str(e)}")
            return None
    
    def set(self, key: str, value: Any) -> None:
        """
        Store a value in the cache.
        
        Args:
            key: The cache key
            value: The value to cache
        """
        cache_path = self._get_cache_path(key)
        
        try:
            cache_entry = {
                'value': value,
                'timestamp': time.time()
            }
            
            with open(cache_path, 'wb') as f:
                pickle.dump(cache_entry, f)
                
            logger.debug(f"Stored value in cache for key: {key}")
            
        except (pickle.PickleError, IOError) as e:
            logger.warning(f"Error storing cache entry for key {key}: {str(e)}")
    
    def invalidate(self, key: str) -> bool:
        """
        Invalidate a cache entry.
        
        Args:
            key: The cache key
            
        Returns:
            True if the entry was invalidated, False otherwise
        """
        cache_path = self._get_cache_path(key)
        
        if os.path.exists(cache_path):
            try:
                os.remove(cache_path)
                logger.debug(f"Invalidated cache entry for key: {key}")
                return True
            except IOError as e:
                logger.warning(f"Error invalidating cache entry for key {key}: {str(e)}")
                
        return False
    
    def clear(self) -> None:
        """
        Clear all cache entries.
        """
        for filename in os.listdir(self.cache_dir):
            if filename.endswith('.pickle'):
                try:
                    os.remove(os.path.join(self.cache_dir, filename))
                except IOError as e:
                    logger.warning(f"Error removing cache file {filename}: {str(e)}")
        
        logger.info(f"Cleared all cache entries from {self.cache_dir}")
    
    def cached(self, ttl: Optional[int] = None) -> Callable[[Callable[..., T]], Callable[..., T]]:
        """
        Decorator for caching function results.
        
        Args:
            ttl: Optional time-to-live in seconds (overrides the instance ttl)
            
        Returns:
            A decorator function
        """
        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            @functools.wraps(func)
            def wrapper(*args, **kwargs) -> T:
                # Generate a cache key for this function call
                func_name = f"{func.__module__}.{func.__qualname__}"
                cache_key = self._get_cache_key(func_name, args, kwargs)
                
                # Check if we have a cached result
                cached_result = self.get(cache_key)
                if cached_result is not None:
                    return cast(T, cached_result)
                
                # Call the function and cache the result
                result = func(*args, **kwargs)
                self.set(cache_key, result)
                
                return result
            return wrapper
        return decorator


class MemoryCache:
    """
    In-memory cache for storing computation results.
    
    This class provides a way to cache expensive computation results in memory,
    allowing them to be reused within a single run.
    """
    
    def __init__(self, maxsize: int = 128, ttl: Optional[int] = None):
        """
        Initialize the memory cache.
        
        Args:
            maxsize: Maximum number of entries to store in the cache
            ttl: Optional time-to-live in seconds for cache entries
        """
        self.maxsize = maxsize
        self.ttl = ttl
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.access_times: Dict[str, float] = {}
        
        logger.debug(f"Initialized memory cache with maxsize: {maxsize}")
    
    def _get_cache_key(self, func_name: str, args: tuple, kwargs: Dict[str, Any]) -> str:
        """
        Generate a cache key for a function call.
        
        Args:
            func_name: The name of the function
            args: Positional arguments to the function
            kwargs: Keyword arguments to the function
            
        Returns:
            A hash-based cache key
        """
        # Create a string representation of the function call
        args_str = str(args)
        kwargs_str = str(sorted(kwargs.items()))
        call_str = f"{func_name}:{args_str}:{kwargs_str}"
        
        # Generate a hash of the call string
        hash_obj = hashlib.md5(call_str.encode('utf-8'))
        return hash_obj.hexdigest()
    
    def _check_size(self) -> None:
        """
        Check if the cache exceeds the maximum size and remove old entries if needed.
        """
        if len(self.cache) <= self.maxsize:
            return
            
        # Sort access times by time (oldest first)
        sorted_keys = sorted(self.access_times.items(), key=lambda x: x[1])
        
        # Remove oldest entries until we're under the maxsize
        to_remove = len(self.cache) - self.maxsize
        for i in range(to_remove):
            key = sorted_keys[i][0]
            del self.cache[key]
            del self.access_times[key]
            
        logger.debug(f"Removed {to_remove} old entries from memory cache")
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.
        
        Args:
            key: The cache key
            
        Returns:
            The cached value, or None if not found or expired
        """
        if key not in self.cache:
            logger.debug(f"Memory cache miss for key: {key}")
            return None
            
        cache_entry = self.cache[key]
        
        # Check if the entry has expired
        if self.ttl is not None:
            timestamp = cache_entry.get('timestamp')
            if timestamp is None or (time.time() - timestamp) > self.ttl:
                logger.debug(f"Memory cache entry expired for key: {key}")
                del self.cache[key]
                del self.access_times[key]
                return None
        
        # Update the access time
        self.access_times[key] = time.time()
            
        logger.debug(f"Memory cache hit for key: {key}")
        return cache_entry.get('value')
    
    def set(self, key: str, value: Any) -> None:
        """
        Store a value in the cache.
        
        Args:
            key: The cache key
            value: The value to cache
        """
        # Check if we need to remove old entries
        self._check_size()
        
        # Store the value
        self.cache[key] = {
            'value': value,
            'timestamp': time.time()
        }
        
        # Update the access time
        self.access_times[key] = time.time()
        
        logger.debug(f"Stored value in memory cache for key: {key}")
    
    def invalidate(self, key: str) -> bool:
        """
        Invalidate a cache entry.
        
        Args:
            key: The cache key
            
        Returns:
            True if the entry was invalidated, False otherwise
        """
        if key in self.cache:
            del self.cache[key]
            del self.access_times[key]
            logger.debug(f"Invalidated memory cache entry for key: {key}")
            return True
            
        return False
    
    def clear(self) -> None:
        """
        Clear all cache entries.
        """
        self.cache.clear()
        self.access_times.clear()
        logger.info("Cleared all memory cache entries")
    
    def cached(self, ttl: Optional[int] = None) -> Callable[[Callable[..., T]], Callable[..., T]]:
        """
        Decorator for caching function results.
        
        Args:
            ttl: Optional time-to-live in seconds (overrides the instance ttl)
            
        Returns:
            A decorator function
        """
        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            @functools.wraps(func)
            def wrapper(*args, **kwargs) -> T:
                # Generate a cache key for this function call
                func_name = f"{func.__module__}.{func.__qualname__}"
                cache_key = self._get_cache_key(func_name, args, kwargs)
                
                # Check if we have a cached result
                cached_result = self.get(cache_key)
                if cached_result is not None:
                    return cast(T, cached_result)
                
                # Call the function and cache the result
                result = func(*args, **kwargs)
                self.set(cache_key, result)
                
                return result
            return wrapper
        return decorator


# Default instances for convenience
memory_cache = MemoryCache()
disk_cache = DiskCache()

# Convenience decorators
def cached_in_memory(ttl: Optional[int] = None) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator for caching function results in memory.
    
    Args:
        ttl: Optional time-to-live in seconds
        
    Returns:
        A decorator function
    """
    return memory_cache.cached(ttl)

def cached_on_disk(ttl: Optional[int] = None) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator for caching function results on disk.
    
    Args:
        ttl: Optional time-to-live in seconds
        
    Returns:
        A decorator function
    """
    return disk_cache.cached(ttl) 