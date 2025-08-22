"""
Strategy Pattern Implementation for Battle Resolution
Provides flexible battle resolution algorithms.
"""

from abc import ABC, abstractmethod
from typing import List, Tuple
from models import DiceRoll, BattleResult, DiceType, SortingStrategy, ComparisonMethod


class AbstractBattleStrategy(ABC):
    """Abstract strategy for resolving battles between dice rolls."""
    
    @abstractmethod
    def resolve_battle(self, attacker_roll: DiceRoll, defender_roll: DiceRoll, 
                      sorting: SortingStrategy, comparison: ComparisonMethod) -> BattleResult:
        """Resolve a battle between attacker and defender rolls."""
        pass


class StandardRiskStrategy(AbstractBattleStrategy):
    """Standard Risk game battle resolution strategy."""
    
    def resolve_battle(self, attacker_roll: DiceRoll, defender_roll: DiceRoll, 
                      sorting: SortingStrategy, comparison: ComparisonMethod) -> BattleResult:
        """Resolve battle using standard Risk rules."""
        attacker_values = attacker_roll.get_sorted_values(sorting)
        defender_values = defender_roll.get_sorted_values(sorting)
        
        attacker_wins = 0
        defender_wins = 0
        
        # Compare highest dice first, then second highest if available
        comparisons = min(len(attacker_values), len(defender_values))
        
        for i in range(comparisons):
            if attacker_values[i] > defender_values[i]:
                attacker_wins += 1
            else:
                defender_wins += 1
        
        return BattleResult(
            attacker_roll=attacker_roll,
            defender_roll=defender_roll,
            attacker_wins=attacker_wins,
            defender_wins=defender_wins
        )


class AlternativeRiskStrategy(AbstractBattleStrategy):
    """Alternative Risk strategy where ties go to attacker."""
    
    def resolve_battle(self, attacker_roll: DiceRoll, defender_roll: DiceRoll, 
                      sorting: SortingStrategy, comparison: ComparisonMethod) -> BattleResult:
        """Resolve battle with ties going to attacker."""
        attacker_values = attacker_roll.get_sorted_values(sorting)
        defender_values = defender_roll.get_sorted_values(sorting)
        
        attacker_wins = 0
        defender_wins = 0
        
        comparisons = min(len(attacker_values), len(defender_values))
        
        for i in range(comparisons):
            if attacker_values[i] >= defender_values[i]:  # >= instead of >
                attacker_wins += 1
            else:
                defender_wins += 1
        
        return BattleResult(
            attacker_roll=attacker_roll,
            defender_roll=defender_roll,
            attacker_wins=attacker_wins,
            defender_wins=defender_wins
        )


class SequentialComparisonStrategy(AbstractBattleStrategy):
    """Strategy that compares dice in sequence rather than highest-to-highest."""
    
    def resolve_battle(self, attacker_roll: DiceRoll, defender_roll: DiceRoll, 
                      sorting: SortingStrategy, comparison: ComparisonMethod) -> BattleResult:
        """Resolve battle using sequential comparison."""
        # For sequential, we don't sort the dice
        attacker_values = attacker_roll.values
        defender_values = defender_roll.values
        
        attacker_wins = 0
        defender_wins = 0
        
        comparisons = min(len(attacker_values), len(defender_values))
        
        for i in range(comparisons):
            if attacker_values[i] > defender_values[i]:
                attacker_wins += 1
            else:
                defender_wins += 1
        
        return BattleResult(
            attacker_roll=attacker_roll,
            defender_roll=defender_roll,
            attacker_wins=attacker_wins,
            defender_wins=defender_wins
        )


class WeightedBattleStrategy(AbstractBattleStrategy):
    """Strategy that applies weights to different dice values."""
    
    def __init__(self, attacker_weights: dict = None, defender_weights: dict = None):
        self.attacker_weights = attacker_weights or {i: 1.0 for i in range(1, 7)}
        self.defender_weights = defender_weights or {i: 1.0 for i in range(1, 7)}
    
    def resolve_battle(self, attacker_roll: DiceRoll, defender_roll: DiceRoll, 
                      sorting: SortingStrategy, comparison: ComparisonMethod) -> BattleResult:
        """Resolve battle using weighted dice values."""
        attacker_values = attacker_roll.get_sorted_values(sorting)
        defender_values = defender_roll.get_sorted_values(sorting)
        
        # Apply weights to dice values
        weighted_attacker = [val * self.attacker_weights.get(val, 1.0) for val in attacker_values]
        weighted_defender = [val * self.defender_weights.get(val, 1.0) for val in defender_values]
        
        attacker_wins = 0
        defender_wins = 0
        
        comparisons = min(len(weighted_attacker), len(weighted_defender))
        
        for i in range(comparisons):
            if weighted_attacker[i] > weighted_defender[i]:
                attacker_wins += 1
            else:
                defender_wins += 1
        
        return BattleResult(
            attacker_roll=attacker_roll,
            defender_roll=defender_roll,
            attacker_wins=attacker_wins,
            defender_wins=defender_wins
        )


class BattleStrategyFactory:
    """Factory for creating battle strategies."""
    
    _strategies = {
        "standard_risk": StandardRiskStrategy,
        "alternative_risk": AlternativeRiskStrategy,
        "sequential": SequentialComparisonStrategy,
        "weighted": WeightedBattleStrategy
    }
    
    @classmethod
    def create_strategy(cls, strategy_type: str, **kwargs) -> AbstractBattleStrategy:
        """Create a battle strategy instance."""
        if strategy_type not in cls._strategies:
            raise ValueError(f"Unknown strategy type: {strategy_type}")
        
        strategy_class = cls._strategies[strategy_type]
        return strategy_class(**kwargs)
    
    @classmethod
    def available_strategies(cls) -> List[str]:
        """Get list of available strategy types."""
        return list(cls._strategies.keys())
    
    @classmethod
    def register_strategy(cls, name: str, strategy_class: type) -> None:
        """Register a new strategy type."""
        cls._strategies[name] = strategy_class


class StrategyContext:
    """Context class for managing battle strategy execution."""
    
    def __init__(self, strategy: AbstractBattleStrategy):
        self._strategy = strategy
    
    def set_strategy(self, strategy: AbstractBattleStrategy) -> None:
        """Change the current strategy."""
        self._strategy = strategy
    
    def execute_battle(self, attacker_roll: DiceRoll, defender_roll: DiceRoll, 
                      sorting: SortingStrategy, comparison: ComparisonMethod) -> BattleResult:
        """Execute battle using current strategy."""
        return self._strategy.resolve_battle(attacker_roll, defender_roll, sorting, comparison)
    
    def get_strategy_info(self) -> str:
        """Get information about current strategy."""
        return f"{self._strategy.__class__.__name__}: {self._strategy.__doc__ or 'No description'}"
