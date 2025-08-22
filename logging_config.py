"""
Enterprise Logging Configuration and Infrastructure
Provides comprehensive logging, monitoring, and observability.
"""

import logging
import logging.handlers
import sys
import json
import threading
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, asdict
from pathlib import Path
import uuid


@dataclass
class LogContext:
    """Context information for structured logging."""
    simulation_id: str
    component: str
    operation: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    correlation_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": threading.current_thread().name,
            "process": record.process
        }
        
        # Add context if available
        if hasattr(record, 'context') and record.context:
            log_data["context"] = record.context.to_dict()
        
        # Add exception information
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info)
            }
        
        # Add custom fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'lineno', 'funcName', 'created', 'msecs', 
                          'relativeCreated', 'thread', 'threadName', 'processName', 'process',
                          'message', 'exc_info', 'exc_text', 'stack_info', 'context']:
                log_data[key] = value
        
        return json.dumps(log_data, ensure_ascii=False)


class ContextualLogger:
    """Logger wrapper that automatically includes context."""
    
    def __init__(self, logger: logging.Logger, default_context: Optional[LogContext] = None):
        self.logger = logger
        self.default_context = default_context
    
    def _log(self, level: int, message: str, context: Optional[LogContext] = None, **kwargs):
        """Internal logging method with context injection."""
        final_context = context or self.default_context
        extra = kwargs.copy()
        if final_context:
            extra['context'] = final_context
        self.logger.log(level, message, extra=extra)
    
    def debug(self, message: str, context: Optional[LogContext] = None, **kwargs):
        self._log(logging.DEBUG, message, context, **kwargs)
    
    def info(self, message: str, context: Optional[LogContext] = None, **kwargs):
        self._log(logging.INFO, message, context, **kwargs)
    
    def warning(self, message: str, context: Optional[LogContext] = None, **kwargs):
        self._log(logging.WARNING, message, context, **kwargs)
    
    def error(self, message: str, context: Optional[LogContext] = None, **kwargs):
        self._log(logging.ERROR, message, context, **kwargs)
    
    def critical(self, message: str, context: Optional[LogContext] = None, **kwargs):
        self._log(logging.CRITICAL, message, context, **kwargs)


class MetricsCollector:
    """Thread-safe metrics collection for application monitoring."""
    
    def __init__(self):
        self._metrics: Dict[str, Any] = {}
        self._counters: Dict[str, int] = {}
        self._timers: Dict[str, List[float]] = {}
        self._gauges: Dict[str, float] = {}
        self._lock = threading.Lock()
    
    def increment_counter(self, name: str, value: int = 1, tags: Optional[Dict[str, str]] = None):
        """Increment a counter metric."""
        with self._lock:
            key = self._build_key(name, tags)
            self._counters[key] = self._counters.get(key, 0) + value
    
    def record_timing(self, name: str, duration: float, tags: Optional[Dict[str, str]] = None):
        """Record a timing metric."""
        with self._lock:
            key = self._build_key(name, tags)
            if key not in self._timers:
                self._timers[key] = []
            self._timers[key].append(duration)
    
    def set_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Set a gauge metric value."""
        with self._lock:
            key = self._build_key(name, tags)
            self._gauges[key] = value
    
    def get_metrics_snapshot(self) -> Dict[str, Any]:
        """Get current snapshot of all metrics."""
        with self._lock:
            snapshot = {
                "timestamp": datetime.utcnow().isoformat(),
                "counters": self._counters.copy(),
                "gauges": self._gauges.copy(),
                "timers": {}
            }
            
            # Calculate timer statistics
            for key, timings in self._timers.items():
                if timings:
                    snapshot["timers"][key] = {
                        "count": len(timings),
                        "sum": sum(timings),
                        "avg": sum(timings) / len(timings),
                        "min": min(timings),
                        "max": max(timings)
                    }
            
            return snapshot
    
    def reset_metrics(self):
        """Reset all metrics."""
        with self._lock:
            self._counters.clear()
            self._timers.clear()
            self._gauges.clear()
    
    def _build_key(self, name: str, tags: Optional[Dict[str, str]]) -> str:
        """Build metric key with tags."""
        if not tags:
            return name
        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}[{tag_str}]"


class PerformanceTimer:
    """Context manager for timing operations."""
    
    def __init__(self, metrics_collector: MetricsCollector, metric_name: str, 
                 tags: Optional[Dict[str, str]] = None):
        self.metrics_collector = metrics_collector
        self.metric_name = metric_name
        self.tags = tags
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is not None:
            duration = time.perf_counter() - self.start_time
            self.metrics_collector.record_timing(self.metric_name, duration, self.tags)


class LoggingManager:
    """Centralized logging management with enterprise features."""
    
    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self._loggers: Dict[str, ContextualLogger] = {}
        self._configured = False
    
    def configure(self, config: Dict[str, Any]) -> None:
        """Configure logging system from configuration."""
        if self._configured:
            return
        
        logging_config = config.get("logging", {})
        
        # Set root logger level
        level = getattr(logging, logging_config.get("level", "INFO").upper())
        logging.getLogger().setLevel(level)
        
        # Clear existing handlers
        for handler in logging.getLogger().handlers[:]:
            logging.getLogger().removeHandler(handler)
        
        # Configure console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(StructuredFormatter())
        logging.getLogger().addHandler(console_handler)
        
        # Configure file handler if specified
        log_file = logging_config.get("file")
        if log_file:
            max_bytes = logging_config.get("max_bytes", 10485760)
            backup_count = logging_config.get("backup_count", 5)
            
            file_handler = logging.handlers.RotatingFileHandler(
                log_file, maxBytes=max_bytes, backupCount=backup_count
            )
            file_handler.setFormatter(StructuredFormatter())
            logging.getLogger().addHandler(file_handler)
        
        self._configured = True
    
    def get_logger(self, name: str, context: Optional[LogContext] = None) -> ContextualLogger:
        """Get or create a contextual logger."""
        if name not in self._loggers:
            base_logger = logging.getLogger(name)
            self._loggers[name] = ContextualLogger(base_logger, context)
        return self._loggers[name]
    
    def create_context(self, simulation_id: str, component: str, operation: str, **kwargs) -> LogContext:
        """Create a new log context."""
        return LogContext(
            simulation_id=simulation_id,
            component=component,
            operation=operation,
            **kwargs
        )
    
    def create_timer(self, metric_name: str, tags: Optional[Dict[str, str]] = None) -> PerformanceTimer:
        """Create a performance timer."""
        return PerformanceTimer(self.metrics_collector, metric_name, tags)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics snapshot."""
        return self.metrics_collector.get_metrics_snapshot()


# Global logging manager instance
logging_manager = LoggingManager()
