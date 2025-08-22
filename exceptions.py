"""
Enterprise Risk Simulation Exception Framework
Provides comprehensive error handling for all simulation scenarios.
"""

from typing import Any, Dict, Optional


class RiskSimulationException(Exception):
    """Base exception for all risk simulation related errors."""
    
    def __init__(self, message: str, error_code: str = "RSE_UNKNOWN", 
                 context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.error_code = error_code
        self.context = context or {}
        self.message = message


class InvalidConfigurationException(RiskSimulationException):
    """Raised when configuration parameters are invalid."""
    
    def __init__(self, parameter: str, value: Any, expected: str):
        message = f"Invalid configuration for '{parameter}': got {value}, expected {expected}"
        super().__init__(message, "RSE_CONFIG_001", {"parameter": parameter, "value": value})


class DiceValidationException(RiskSimulationException):
    """Raised when dice configuration is invalid."""
    
    def __init__(self, dice_type: str, issue: str):
        message = f"Dice validation failed for {dice_type}: {issue}"
        super().__init__(message, "RSE_DICE_001", {"dice_type": dice_type, "issue": issue})


class SimulationExecutionException(RiskSimulationException):
    """Raised when simulation execution fails."""
    
    def __init__(self, iteration: int, cause: str):
        message = f"Simulation failed at iteration {iteration}: {cause}"
        super().__init__(message, "RSE_SIM_001", {"iteration": iteration, "cause": cause})


class MetricsCollectionException(RiskSimulationException):
    """Raised when metrics collection fails."""
    
    def __init__(self, metric_name: str, cause: str):
        message = f"Failed to collect metric '{metric_name}': {cause}"
        super().__init__(message, "RSE_METRICS_001", {"metric_name": metric_name, "cause": cause})


class DatabaseException(RiskSimulationException):
    """Raised when database operations fail."""
    
    def __init__(self, operation: str, cause: str):
        message = f"Database operation '{operation}' failed: {cause}"
        super().__init__(message, "RSE_DB_001", {"operation": operation, "cause": cause})


class CacheException(RiskSimulationException):
    """Raised when cache operations fail."""
    
    def __init__(self, operation: str, key: str, cause: str):
        message = f"Cache operation '{operation}' failed for key '{key}': {cause}"
        super().__init__(message, "RSE_CACHE_001", {"operation": operation, "key": key, "cause": cause})
