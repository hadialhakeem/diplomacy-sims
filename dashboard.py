"""
Enterprise Metrics Dashboard and Reporting System
Real-time monitoring and visualization for Risk Simulation.
"""

import json
import threading
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import socketserver
from logging_config import logging_manager


@dataclass
class DashboardMetric:
    """Structured metric for dashboard display."""
    name: str
    value: float
    unit: str
    timestamp: datetime
    tags: Dict[str, str]
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "timestamp": self.timestamp.isoformat(),
            "tags": self.tags,
            "description": self.description
        }


class MetricAggregator:
    """Aggregates and processes metrics for dashboard display."""
    
    def __init__(self, window_size_minutes: int = 60):
        self.window_size = timedelta(minutes=window_size_minutes)
        self._metrics_history: List[DashboardMetric] = []
        self._lock = threading.Lock()
    
    def add_metric(self, metric: DashboardMetric) -> None:
        """Add a metric to the aggregator."""
        with self._lock:
            self._metrics_history.append(metric)
            self._cleanup_old_metrics()
    
    def get_current_metrics(self) -> List[Dict[str, Any]]:
        """Get current metrics within the time window."""
        with self._lock:
            cutoff_time = datetime.now() - self.window_size
            current_metrics = [
                metric.to_dict() for metric in self._metrics_history
                if metric.timestamp >= cutoff_time
            ]
            return current_metrics
    
    def get_aggregated_metrics(self) -> Dict[str, Any]:
        """Get aggregated statistics."""
        with self._lock:
            if not self._metrics_history:
                return {}
            
            # Group metrics by name
            grouped = {}
            for metric in self._metrics_history:
                if metric.name not in grouped:
                    grouped[metric.name] = []
                grouped[metric.name].append(metric.value)
            
            # Calculate statistics
            aggregated = {}
            for name, values in grouped.items():
                aggregated[name] = {
                    "count": len(values),
                    "sum": sum(values),
                    "avg": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "latest": values[-1] if values else 0
                }
            
            return aggregated
    
    def _cleanup_old_metrics(self) -> None:
        """Remove metrics outside the time window."""
        cutoff_time = datetime.now() - self.window_size
        self._metrics_history = [
            metric for metric in self._metrics_history
            if metric.timestamp >= cutoff_time
        ]


class DashboardRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the dashboard web interface."""
    
    def do_GET(self):
        """Handle GET requests."""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/':
            self._serve_dashboard_html()
        elif parsed_path.path == '/api/metrics':
            self._serve_metrics_api()
        elif parsed_path.path == '/api/aggregated':
            self._serve_aggregated_api()
        elif parsed_path.path == '/api/health':
            self._serve_health_api()
        else:
            self._send_404()
    
    def _serve_dashboard_html(self):
        """Serve the main dashboard HTML page."""
        html_content = self._get_dashboard_html()
        self._send_response(200, html_content, 'text/html')
    
    def _serve_metrics_api(self):
        """Serve current metrics as JSON."""
        metrics = self.server.metric_aggregator.get_current_metrics()
        self._send_json_response({"metrics": metrics})
    
    def _serve_aggregated_api(self):
        """Serve aggregated metrics as JSON."""
        aggregated = self.server.metric_aggregator.get_aggregated_metrics()
        self._send_json_response({"aggregated": aggregated})
    
    def _serve_health_api(self):
        """Serve health check response."""
        health_data = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": time.time() - self.server.start_time
        }
        self._send_json_response(health_data)
    
    def _send_response(self, status_code: int, content: str, content_type: str):
        """Send HTTP response with content."""
        self.send_response(status_code)
        self.send_header('Content-type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(content.encode('utf-8'))
    
    def _send_json_response(self, data: Dict[str, Any]):
        """Send JSON response."""
        json_content = json.dumps(data, indent=2)
        self._send_response(200, json_content, 'application/json')
    
    def _send_404(self):
        """Send 404 Not Found response."""
        self._send_response(404, "Not Found", 'text/plain')
    
    def _get_dashboard_html(self) -> str:
        """Generate dashboard HTML content."""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Risk Simulation Dashboard</title>
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .header { background: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .metric-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .metric-value { font-size: 2em; font-weight: bold; color: #2c3e50; }
        .metric-label { color: #7f8c8d; margin-top: 5px; }
        .chart-container { margin-top: 20px; height: 200px; background: #ecf0f1; border-radius: 4px; }
        .status-indicator { display: inline-block; width: 12px; height: 12px; border-radius: 50%; margin-right: 8px; }
        .status-healthy { background: #27ae60; }
        .refresh-btn { background: #3498db; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; }
        .refresh-btn:hover { background: #2980b9; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🎲 Risk Simulation Enterprise Dashboard</h1>
        <p><span class="status-indicator status-healthy"></span>System Status: Operational</p>
        <button class="refresh-btn" onclick="refreshData()">Refresh Data</button>
    </div>
    
    <div class="metrics-grid" id="metricsGrid">
        <!-- Metrics will be populated here -->
    </div>
    
    <script>
        function refreshData() {
            fetch('/api/aggregated')
                .then(response => response.json())
                .then(data => updateDashboard(data))
                .catch(error => console.error('Error:', error));
        }
        
        function updateDashboard(data) {
            const grid = document.getElementById('metricsGrid');
            grid.innerHTML = '';
            
            for (const [name, stats] of Object.entries(data.aggregated || {})) {
                const card = document.createElement('div');
                card.className = 'metric-card';
                card.innerHTML = `
                    <div class="metric-value">${stats.latest.toFixed(2)}</div>
                    <div class="metric-label">${name}</div>
                    <div style="margin-top: 10px; font-size: 0.9em; color: #95a5a6;">
                        Count: ${stats.count} | Avg: ${stats.avg.toFixed(2)} | Min: ${stats.min} | Max: ${stats.max}
                    </div>
                `;
                grid.appendChild(card);
            }
        }
        
        // Auto-refresh every 5 seconds
        setInterval(refreshData, 5000);
        
        // Initial load
        refreshData();
    </script>
</body>
</html>
        """
    
    def log_message(self, format, *args):
        """Override to use our logging system."""
        logger = logging_manager.get_logger("dashboard")
        logger.info(f"{self.address_string()} - {format % args}")


class DashboardServer:
    """Enterprise dashboard server with metrics visualization."""
    
    def __init__(self, port: int = 8080, host: str = 'localhost'):
        self.port = port
        self.host = host
        self.metric_aggregator = MetricAggregator()
        self.server = None
        self.server_thread = None
        self.logger = logging_manager.get_logger("dashboard")
    
    def start(self) -> None:
        """Start the dashboard server."""
        try:
            # Create server with custom attributes
            self.server = HTTPServer((self.host, self.port), DashboardRequestHandler)
            self.server.metric_aggregator = self.metric_aggregator
            self.server.start_time = time.time()
            
            # Start server in background thread
            self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.server_thread.start()
            
            self.logger.info(f"Dashboard server started on http://{self.host}:{self.port}")
            
        except Exception as e:
            self.logger.error(f"Failed to start dashboard server: {e}")
            raise
    
    def stop(self) -> None:
        """Stop the dashboard server."""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.logger.info("Dashboard server stopped")
    
    def add_metric(self, name: str, value: float, unit: str = "", 
                   tags: Optional[Dict[str, str]] = None, description: str = "") -> None:
        """Add a metric to the dashboard."""
        metric = DashboardMetric(
            name=name,
            value=value,
            unit=unit,
            timestamp=datetime.now(),
            tags=tags or {},
            description=description
        )
        self.metric_aggregator.add_metric(metric)
    
    def is_running(self) -> bool:
        """Check if server is running."""
        return self.server is not None and self.server_thread is not None and self.server_thread.is_alive()


class MetricsReporter:
    """Automated metrics reporting service."""
    
    def __init__(self, dashboard_server: DashboardServer, report_interval: int = 10):
        self.dashboard_server = dashboard_server
        self.report_interval = report_interval
        self.running = False
        self.thread = None
        self.logger = logging_manager.get_logger("metrics_reporter")
    
    def start(self) -> None:
        """Start metrics reporting."""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._report_loop, daemon=True)
        self.thread.start()
        self.logger.info("Metrics reporter started")
    
    def stop(self) -> None:
        """Stop metrics reporting."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)
        self.logger.info("Metrics reporter stopped")
    
    def _report_loop(self) -> None:
        """Main reporting loop."""
        while self.running:
            try:
                # Get metrics from logging manager
                metrics_data = logging_manager.get_metrics()
                
                # Report counter metrics
                for name, value in metrics_data.get("counters", {}).items():
                    self.dashboard_server.add_metric(name, value, "count")
                
                # Report gauge metrics
                for name, value in metrics_data.get("gauges", {}).items():
                    self.dashboard_server.add_metric(name, value, "gauge")
                
                # Report timer metrics (average)
                for name, stats in metrics_data.get("timers", {}).items():
                    self.dashboard_server.add_metric(f"{name}_avg", stats["avg"], "seconds")
                    self.dashboard_server.add_metric(f"{name}_count", stats["count"], "count")
                
                time.sleep(self.report_interval)
                
            except Exception as e:
                self.logger.error(f"Error in metrics reporting: {e}")
                time.sleep(1)  # Brief pause before retry
