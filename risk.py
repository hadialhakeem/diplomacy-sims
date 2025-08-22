"""
Enterprise Risk Dice Simulation Engine
A comprehensive, scalable, and enterprise-grade simulation platform.
"""

import random
import time
import yaml
import psutil
from typing import List, Optional
from datetime import datetime
from pathlib import Path

# Import our enterprise modules
from models import (
    DiceType, SortingStrategy, ComparisonMethod, SimulationConfiguration,
    SimulationResult, SimulationMetrics, SimulationObserver
)
from factories import factory_registry
from strategies import BattleStrategyFactory, StrategyContext
from logging_config import logging_manager, LogContext
from dashboard import DashboardServer, MetricsReporter
from dependency_injection import container, Injectable, LifecycleScope
from exceptions import (
    RiskSimulationException, InvalidConfigurationException,
    SimulationExecutionException
)


@Injectable(lifecycle=LifecycleScope.SINGLETON)
class EnterpriseRiskSimulationEngine:
    """
    Enterprise-grade Risk dice simulation engine with comprehensive
    monitoring, logging, metrics, and extensibility features.
    """
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = Path(config_path)
        self.configuration: Optional[SimulationConfiguration] = None
        self.dashboard_server: Optional[DashboardServer] = None
        self.metrics_reporter: Optional[MetricsReporter] = None
        self.observers: List[SimulationObserver] = []
        self.random_generator = random.Random()
        
        # Setup logging
        self._setup_logging()
        self.logger = logging_manager.get_logger("simulation_engine")
        
        # Load configuration
        self._load_configuration()
        
        # Initialize components
        self._initialize_components()
    
    def _setup_logging(self) -> None:
        """Initialize enterprise logging system."""
        try:
            with open(self.config_path, 'r') as f:
                config_data = yaml.safe_load(f)
            logging_manager.configure(config_data)
        except Exception as e:
            # Fallback to basic logging
            logging_manager.configure({})
            print(f"Warning: Could not load logging config: {e}")
    
    def _load_configuration(self) -> None:
        """Load simulation configuration from YAML file."""
        try:
            if not self.config_path.exists():
                raise InvalidConfigurationException(
                    "config_file", self.config_path, "existing YAML file"
                )
            
            with open(self.config_path, 'r') as f:
                config_data = yaml.safe_load(f)
            
            config_factory = factory_registry.get("configuration_factory")
            self.configuration = config_factory.create_from_dict(config_data)
            
            # Set random seed if specified
            if self.configuration.random_seed is not None:
                self.random_generator.seed(self.configuration.random_seed)
            
            self.logger.info("Configuration loaded successfully", 
                           extra={"config_path": str(self.config_path)})
            
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            raise
    
    def _initialize_components(self) -> None:
        """Initialize dashboard and monitoring components."""
        try:
            # Initialize dashboard server
            self.dashboard_server = DashboardServer(port=8080)
            self.dashboard_server.start()
            
            # Initialize metrics reporter
            self.metrics_reporter = MetricsReporter(self.dashboard_server)
            self.metrics_reporter.start()
            
            # Register self as observer for automatic metrics
            self.add_observer(EnterpriseMetricsObserver(self.dashboard_server))
            
            self.logger.info("Enterprise components initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize components: {e}")
            raise
    
    def add_observer(self, observer: SimulationObserver) -> None:
        """Add a simulation observer."""
        self.observers.append(observer)
        self.logger.debug(f"Added observer: {observer.__class__.__name__}")
    
    def remove_observer(self, observer: SimulationObserver) -> None:
        """Remove a simulation observer."""
        if observer in self.observers:
            self.observers.remove(observer)
            self.logger.debug(f"Removed observer: {observer.__class__.__name__}")
    
    def run_simulation(self) -> SimulationResult:
        """Execute the complete simulation with enterprise features."""
        if not self.configuration:
            raise SimulationExecutionException(0, "No configuration loaded")
        
        simulation_id = f"sim_{int(time.time())}"
        context = logging_manager.create_context(
            simulation_id=simulation_id,
            component="simulation_engine",
            operation="run_simulation"
        )
        
        self.logger.info("Starting enterprise risk simulation", context=context)
        
        # Notify observers of simulation start
        for observer in self.observers:
            observer.on_simulation_started(self.configuration)
        
        try:
            start_time = datetime.now()
            
            # Initialize simulation result
            result = SimulationResult(
                configuration=self.configuration,
                metrics=SimulationMetrics(),
                simulation_id=simulation_id,
                start_time=start_time
            )
            
            # Execute simulation with performance monitoring
            with logging_manager.create_timer("simulation_total_time"):
                self._execute_simulation_batches(result, context)
            
            # Finalize result
            result.end_time = datetime.now()
            result.metrics.execution_time_seconds = (result.end_time - start_time).total_seconds()
            
            # Calculate performance metrics
            self._calculate_performance_metrics(result)
            
            # Notify observers of completion
            for observer in self.observers:
                observer.on_simulation_completed(result)
            
            self.logger.info("Simulation completed successfully", 
                           context=context,
                           extra={"total_battles": result.metrics.total_battles,
                                 "execution_time": result.metrics.execution_time_seconds})
            
            return result
            
        except Exception as e:
            self.logger.error(f"Simulation failed: {e}", context=context, exc_info=True)
            raise SimulationExecutionException(0, str(e))
    
    def _execute_simulation_batches(self, result: SimulationResult, context: LogContext) -> None:
        """Execute simulation in batches for better monitoring."""
        total_iterations = self.configuration.iterations
        batch_size = self.configuration.batch_size
        total_batches = (total_iterations + batch_size - 1) // batch_size
        
        dice_factory = factory_registry.get("dice_factory")
        strategy_context = StrategyContext(
            BattleStrategyFactory.create_strategy("standard_risk")
        )
        
        current_iteration = 0
        
        for batch_num in range(total_batches):
            batch_start = time.perf_counter()
            iterations_in_batch = min(batch_size, total_iterations - current_iteration)
            
            self.logger.debug(f"Processing batch {batch_num + 1}/{total_batches}", 
                            context=context)
            
            # Execute batch
            for _ in range(iterations_in_batch):
                battle_result = self._execute_single_battle(
                    dice_factory, strategy_context, current_iteration
                )
                
                # Update metrics
                result.metrics.total_battles += 1
                result.metrics.attacker_total_wins += battle_result.attacker_wins
                result.metrics.defender_total_wins += battle_result.defender_wins
                
                # Store battle result (limit storage for memory efficiency)
                if len(result.battle_history) < 1000:
                    result.battle_history.append(battle_result)
                
                # Notify observers
                for observer in self.observers:
                    observer.on_battle_completed(battle_result)
                
                current_iteration += 1
            
            # Calculate batch timing
            batch_time = time.perf_counter() - batch_start
            result.metrics.average_battle_time_ms = (batch_time * 1000) / iterations_in_batch
            
            # Notify observers of batch completion
            for observer in self.observers:
                observer.on_batch_completed(batch_num + 1, total_batches)
            
            # Memory usage monitoring
            process = psutil.Process()
            result.metrics.memory_usage_mb = process.memory_info().rss / 1024 / 1024
    
    def _execute_single_battle(self, dice_factory, strategy_context, iteration: int):
        """Execute a single battle between attacker and defender."""
        try:
            # Create dice rolls
            attacker_roll = dice_factory.create_dice_roll(
                self.configuration.attacker_dice, self.random_generator
            )
            defender_roll = dice_factory.create_dice_roll(
                self.configuration.defender_dice, self.random_generator
            )
            
            # Resolve battle
            battle_result = strategy_context.execute_battle(
                attacker_roll, defender_roll,
                self.configuration.sorting_strategy,
                self.configuration.comparison_method
            )
            
            return battle_result
            
        except Exception as e:
            raise SimulationExecutionException(iteration, str(e))
    
    def _calculate_performance_metrics(self, result: SimulationResult) -> None:
        """Calculate additional performance metrics."""
        if result.metrics.execution_time_seconds > 0:
            result.metrics.battles_per_second = (
                result.metrics.total_battles / result.metrics.execution_time_seconds
            )
    
    def get_simulation_report(self, result: SimulationResult) -> str:
        """Generate comprehensive simulation report."""
        report = [
            "🎲 ENTERPRISE RISK SIMULATION REPORT",
            "=" * 50,
            f"Simulation ID: {result.simulation_id}",
            f"Start Time: {result.start_time}",
            f"End Time: {result.end_time}",
            f"Duration: {result.metrics.execution_time_seconds:.3f} seconds",
            "",
            "BATTLE RESULTS:",
            f"  Total Battles: {result.metrics.total_battles:,}",
            f"  Attacker Wins: {result.metrics.attacker_total_wins:,} ({result.metrics.attacker_win_percentage:.2f}%)",
            f"  Defender Wins: {result.metrics.defender_total_wins:,} ({result.metrics.defender_win_percentage:.2f}%)",
            "",
            "PERFORMANCE METRICS:",
            f"  Battles/Second: {result.metrics.battles_per_second:,.0f}",
            f"  Avg Battle Time: {result.metrics.average_battle_time_ms:.3f}ms",
            f"  Memory Usage: {result.metrics.memory_usage_mb:.1f}MB",
            "",
            "CONFIGURATION:",
            f"  Attacker Dice: {result.configuration.attacker_dice.count}d{result.configuration.attacker_dice.sides}",
            f"  Defender Dice: {result.configuration.defender_dice.count}d{result.configuration.defender_dice.sides}",
            f"  Strategy: {result.configuration.sorting_strategy.value}",
            f"  Random Seed: {result.configuration.random_seed}",
            "",
            "Dashboard available at: http://localhost:8080",
            "=" * 50
        ]
        
        return "\n".join(report)
    
    def shutdown(self) -> None:
        """Gracefully shutdown the simulation engine."""
        self.logger.info("Shutting down simulation engine")
        
        if self.metrics_reporter:
            self.metrics_reporter.stop()
        
        if self.dashboard_server:
            self.dashboard_server.stop()
        
        self.logger.info("Simulation engine shutdown complete")


class EnterpriseMetricsObserver:
    """Observer that reports metrics to the dashboard."""
    
    def __init__(self, dashboard_server: DashboardServer):
        self.dashboard_server = dashboard_server
        self.batch_count = 0
    
    def on_simulation_started(self, config: SimulationConfiguration) -> None:
        """Report simulation start metrics."""
        self.dashboard_server.add_metric("simulation_iterations", config.iterations, "count")
        self.dashboard_server.add_metric("batch_size", config.batch_size, "count")
    
    def on_battle_completed(self, result) -> None:
        """Report individual battle metrics."""
        winner = result.get_winner()
        if winner == DiceType.ATTACKER:
            self.dashboard_server.add_metric("attacker_battles_won", 1, "count")
        elif winner == DiceType.DEFENDER:
            self.dashboard_server.add_metric("defender_battles_won", 1, "count")
    
    def on_batch_completed(self, batch_number: int, total_batches: int) -> None:
        """Report batch completion metrics."""
        self.batch_count += 1
        progress = (batch_number / total_batches) * 100
        self.dashboard_server.add_metric("simulation_progress", progress, "percent")
        self.dashboard_server.add_metric("batches_completed", self.batch_count, "count")
    
    def on_simulation_completed(self, result: SimulationResult) -> None:
        """Report final simulation metrics."""
        self.dashboard_server.add_metric("total_simulation_time", 
                                        result.metrics.execution_time_seconds, "seconds")
        self.dashboard_server.add_metric("battles_per_second", 
                                        result.metrics.battles_per_second, "rate")


def main():
    """Main entry point for the enterprise simulation."""
    try:
        # Initialize dependency injection container
        container.register_singleton(EnterpriseRiskSimulationEngine)
        
        # Resolve and run simulation
        engine = container.resolve(EnterpriseRiskSimulationEngine)
        
        print("🚀 Starting Enterprise Risk Simulation Engine...")
        print("Dashboard will be available at: http://localhost:8080")
        print()
        
        # Run the simulation
        result = engine.run_simulation()
        
        # Display results
        report = engine.get_simulation_report(result)
        print(report)
        
        # Keep dashboard running for a bit
        print("\nDashboard is running. Press Ctrl+C to exit...")
        try:
            time.sleep(30)  # Keep running for 30 seconds
        except KeyboardInterrupt:
            print("\nShutting down...")
        
        # Graceful shutdown
        engine.shutdown()
        
    except Exception as e:
        print(f"❌ Simulation failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
