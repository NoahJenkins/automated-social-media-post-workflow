"""
Metrics utilities for tracking latency and performance across workflow nodes.

This module provides decorators and helpers for instrumenting LangGraph nodes
with latency tracking, following LangSmith observability best practices.
"""

import time
import logging
from functools import wraps
from typing import Any, Callable, Dict

logger = logging.getLogger(__name__)


def track_node_latency(node_name: str) -> Callable:
    """
    Decorator to track execution latency for a LangGraph node.
    
    Adds the node's execution time to state["node_latencies"] dict.
    
    Args:
        node_name: Name of the node for latency tracking
    
    Returns:
        Decorated function that tracks latency
    
    Usage:
        @track_node_latency("researcher")
        def researcher_node(state: Dict[str, Any]) -> Dict[str, Any]:
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(state: Dict[str, Any]) -> Dict[str, Any]:
            start_time = time.perf_counter()
            
            try:
                result = func(state)
            except Exception as e:
                # Track error in state
                errors = state.get("errors", [])
                errors.append(f"{node_name}: {str(e)}")
                
                # Still track latency even on failure
                elapsed = time.perf_counter() - start_time
                latencies = state.get("node_latencies", {})
                latencies[node_name] = round(elapsed, 3)
                
                raise
            
            elapsed = time.perf_counter() - start_time
            
            # Ensure result is a dict
            if not isinstance(result, dict):
                result = {}
            
            # Update node_latencies in result
            latencies = state.get("node_latencies", {}).copy()
            latencies[node_name] = round(elapsed, 3)
            result["node_latencies"] = latencies
            
            logger.debug(f"Node '{node_name}' completed in {elapsed:.3f}s")
            
            return result
        
        return wrapper
    return decorator


def wrap_node_with_latency(node_func: Callable, node_name: str) -> Callable:
    """
    Wrap an existing node function with latency tracking without decorators.
    
    Useful for wrapping imported node functions that can't be decorated directly.
    
    Args:
        node_func: The original node function
        node_name: Name of the node for latency tracking
    
    Returns:
        Wrapped function with latency tracking
    
    Usage:
        from src.agents.researcher import researcher_node
        tracked_researcher = wrap_node_with_latency(researcher_node, "researcher")
    """
    @wraps(node_func)
    def wrapper(state: Dict[str, Any]) -> Dict[str, Any]:
        start_time = time.perf_counter()
        
        try:
            result = node_func(state)
        except Exception as e:
            errors = list(state.get("errors") or [])
            errors.append(f"{node_name}: {str(e)}")
            
            elapsed = time.perf_counter() - start_time
            latencies = dict(state.get("node_latencies") or {})
            latencies[node_name] = round(elapsed, 3)
            
            raise
        
        elapsed = time.perf_counter() - start_time
        
        if not isinstance(result, dict):
            result = {}
        
        # Merge latencies from state with new measurement
        latencies = dict(state.get("node_latencies") or {})
        latencies[node_name] = round(elapsed, 3)
        result["node_latencies"] = latencies
        
        # Track image generation attempts specifically
        if node_name == "image_generator":
            attempts = (state.get("image_generation_attempts") or 0) + 1
            result["image_generation_attempts"] = attempts
        
        return result
    
    return wrapper


def calculate_latency_stats(node_latencies: Dict[str, float]) -> Dict[str, Any]:
    """
    Calculate summary statistics from node latencies.
    
    Args:
        node_latencies: Dict mapping node names to latency in seconds
    
    Returns:
        Dict with total, mean, min, max, and slowest node
    """
    if not node_latencies:
        return {
            "total": 0,
            "mean": 0,
            "min": 0,
            "max": 0,
            "slowest_node": None,
            "node_count": 0
        }
    
    latencies = list(node_latencies.values())
    slowest_node = max(node_latencies, key=node_latencies.get)
    
    return {
        "total": round(sum(latencies), 3),
        "mean": round(sum(latencies) / len(latencies), 3),
        "min": round(min(latencies), 3),
        "max": round(max(latencies), 3),
        "slowest_node": slowest_node,
        "node_count": len(latencies)
    }
