"""
Enterprise Factory Pattern Implementation
Provides flexible object creation and dependency management.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Type, Optional, List
import random
from datetime import datetime

from models import (
    DiceConfiguration, DiceRoll, DiceType, SortingStrategy, 
    ComparisonMethod, SimulationConfiguration, SimulationMetrics
)
from exceptions import InvalidConfigurationException, DiceValidationException


class AbstractDiceFactory(ABC):
    """Abstract factory for creating dice-related objects."""
    
    @abstractmethod
    def create_dice_configuration(self, config_data: Dict[str, Any], dice_type: DiceType) -> DiceConfiguration:
        """Create dice configuration from configuration data."""
        pass
    
    @abstractmethod
    def create_dice_roll(self, config: DiceConfiguration, random_generator: random.Random) -> DiceRoll:
        """Create a dice roll using the given configuration."""
        pass


class StandardDiceFactory(AbstractDiceFactory):
    """Standard implementation of dice factory."""
    
    def create_dice_configuration(self, config_data: Dict[str, Any], dice_type: DiceType) -> DiceConfiguration:
        """Create dice configuration with validation."""
        try:
            return DiceConfiguration(
                count=config_data.get("count", 1),
                sides=config_data.get("sides", 6),
                min_value=config_data.get("min_value", 1),
                max_value=config_data.get("max_value", 6),
                dice_type=dice_type
            )
        except ValueError as e:
            raise DiceValidationException(dice_type.value, str(e))
    
    def create_dice_roll(self, config: DiceConfiguration, random_generator: random.Random) -> DiceRoll:
        """Create a dice roll with random values."""
        values = [
            random_generator.randint(config.min_value, config.max_value)
            for _ in range(config.count)
        ]
        return DiceRoll(values=values, dice_type=config.dice_type)


class WeightedDiceFactory(AbstractDiceFactory):
    """Factory for creating weighted dice (for advanced simulations)."""
    
    def __init__(self, weights: Optional[Dict[int, float]] = None):
        self.weights = weights or {}
    
    def create_dice_configuration(self, config_data: Dict[str, Any], dice_type: DiceType) -> DiceConfiguration:
        """Create weighted dice configuration."""
        config = DiceConfiguration(
            count=config_data.get("count", 1),
            sides=config_data.get("sides", 6),
            min_value=config_data.get("min_value", 1),
            max_value=config_data.get("max_value", 6),
            dice_type=dice_type
        )
        return config
    
    def create_dice_roll(self, config: DiceConfiguration, random_generator: random.Random) -> DiceRoll:
        """Create weighted dice roll."""
        values = []
        for _ in range(config.count):
            if self.weights:
                # Weighted random selection
                choices = list(range(config.min_value, config.max_value + 1))
                weights = [self.weights.get(choice, 1.0) for choice in choices]
                value = random_generator.choices(choices, weights=weights)[0]
            else:
                value = random_generator.randint(config.min_value, config.max_value)
            values.append(value)
        
        return DiceRoll(values=values, dice_type=config.dice_type)


class ConfigurationFactory:
    """Factory for creating simulation configurations."""
    
    def __init__(self, dice_factory: AbstractDiceFactory):
        self.dice_factory = dice_factory
    
    def create_from_dict(self, config_data: Dict[str, Any]) -> SimulationConfiguration:
        """Create simulation configuration from dictionary."""
        try:
            game_config = config_data.get("game", {})
            simulation_config = game_config.get("simulation", {})
            dice_config = game_config.get("dice", {})
            strategy_config = game_config.get("strategy", {})
            
            # Create dice configurations
            attacker_dice = self.dice_factory.create_dice_configuration(
                dice_config.get("attacker", {}), DiceType.ATTACKER
            )
            defender_dice = self.dice_factory.create_dice_configuration(
                dice_config.get("defender", {}), DiceType.DEFENDER
            )
            
            # Parse strategy enums
            sorting_strategy = SortingStrategy.DESCENDING
            if strategy_config.get("sorting") == "ascending":
                sorting_strategy = SortingStrategy.ASCENDING
            
            comparison_method = ComparisonMethod.HIGHEST_TO_HIGHEST
            if strategy_config.get("comparison_method") == "sequential":
                comparison_method = ComparisonMethod.SEQUENTIAL
            
            config = SimulationConfiguration(
                iterations=simulation_config.get("iterations", 1000000),
                random_seed=simulation_config.get("random_seed"),
                batch_size=simulation_config.get("batch_size", 10000),
                attacker_dice=attacker_dice,
                defender_dice=defender_dice,
                sorting_strategy=sorting_strategy,
                comparison_method=comparison_method
            )
            
            config.validate()
            return config
            
        except (KeyError, ValueError, TypeError) as e:
            raise InvalidConfigurationException("simulation_config", str(e), "valid configuration dictionary")


class MetricsFactory:
    """Factory for creating metrics objects."""
    
    @staticmethod
    def create_empty_metrics() -> SimulationMetrics:
        """Create empty metrics object."""
        return SimulationMetrics()
    
    @staticmethod
    def create_from_battle_results(battle_results: List[Any], execution_time: float) -> SimulationMetrics:
        """Create metrics from battle results."""
        metrics = SimulationMetrics()
        metrics.total_battles = len(battle_results)
        metrics.execution_time_seconds = execution_time
        
        if battle_results:
            metrics.average_battle_time_ms = (execution_time * 1000) / len(battle_results)
        
        # Count wins
        for result in battle_results:
            if hasattr(result, 'attacker_wins') and hasattr(result, 'defender_wins'):
                metrics.attacker_total_wins += result.attacker_wins
                metrics.defender_total_wins += result.defender_wins
        
        return metrics


class FactoryRegistry:
    """Registry for managing factory instances."""
    
    def __init__(self):
        self._factories: Dict[str, Any] = {}
        self._default_factories()
    
    def _default_factories(self):
        """Register default factory implementations."""
        self.register("dice_factory", StandardDiceFactory())
        self.register("weighted_dice_factory", WeightedDiceFactory())
        self.register("configuration_factory", ConfigurationFactory(self.get("dice_factory")))
        self.register("metrics_factory", MetricsFactory())
    
    def register(self, name: str, factory: Any) -> None:
        """Register a factory instance."""
        self._factories[name] = factory
    
    def get(self, name: str) -> Any:
        """Get a factory instance."""
        if name not in self._factories:
            raise KeyError(f"Factory '{name}' not registered")
        return self._factories[name]
    
    def list_factories(self) -> List[str]:
        """List all registered factory names."""
        return list(self._factories.keys())


# Global factory registry instance
factory_registry = FactoryRegistry()
