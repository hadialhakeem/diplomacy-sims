"""
Enterprise Data Models for Risk Simulation
Comprehensive dataclasses with validation and serialization support.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Protocol
from datetime import datetime
from enum import Enum
import json
import uuid


class DiceType(Enum):
    """Enumeration of supported dice types."""
    ATTACKER = "attacker"
    DEFENDER = "defender"


class SortingStrategy(Enum):
    """Enumeration of dice sorting strategies."""
    ASCENDING = "ascending"
    DESCENDING = "descending"


class ComparisonMethod(Enum):
    """Enumeration of dice comparison methods."""
    HIGHEST_TO_HIGHEST = "highest_to_highest"
    SEQUENTIAL = "sequential"


@dataclass(frozen=True)
class DiceConfiguration:
    """Immutable configuration for dice parameters."""
    count: int
    sides: int
    min_value: int
    max_value: int
    dice_type: DiceType
    
    def __post_init__(self):
        if self.count <= 0:
            raise ValueError(f"Dice count must be positive, got {self.count}")
        if self.sides <= 0:
            raise ValueError(f"Dice sides must be positive, got {self.sides}")
        if self.min_value >= self.max_value:
            raise ValueError(f"Min value must be less than max value")
        if self.min_value < 1 or self.max_value > self.sides:
            raise ValueError(f"Dice values must be between 1 and {self.sides}")


@dataclass
class DiceRoll:
    """Represents a single dice roll with metadata."""
    values: List[int]
    dice_type: DiceType
    timestamp: datetime = field(default_factory=datetime.now)
    roll_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def get_sorted_values(self, strategy: SortingStrategy = SortingStrategy.DESCENDING) -> List[int]:
        """Return sorted dice values based on strategy."""
        return sorted(self.values, reverse=(strategy == SortingStrategy.DESCENDING))
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "values": self.values,
            "dice_type": self.dice_type.value,
            "timestamp": self.timestamp.isoformat(),
            "roll_id": self.roll_id
        }


@dataclass
class BattleResult:
    """Result of a single battle between attacker and defender."""
    attacker_roll: DiceRoll
    defender_roll: DiceRoll
    attacker_wins: int
    defender_wins: int
    battle_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    
    def get_winner(self) -> Optional[DiceType]:
        """Determine the winner of the battle."""
        if self.attacker_wins > self.defender_wins:
            return DiceType.ATTACKER
        elif self.defender_wins > self.attacker_wins:
            return DiceType.DEFENDER
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "attacker_roll": self.attacker_roll.to_dict(),
            "defender_roll": self.defender_roll.to_dict(),
            "attacker_wins": self.attacker_wins,
            "defender_wins": self.defender_wins,
            "battle_id": self.battle_id,
            "timestamp": self.timestamp.isoformat(),
            "winner": self.get_winner().value if self.get_winner() else None
        }


@dataclass
class SimulationConfiguration:
    """Complete configuration for simulation parameters."""
    iterations: int
    random_seed: Optional[int]
    batch_size: int
    attacker_dice: DiceConfiguration
    defender_dice: DiceConfiguration
    sorting_strategy: SortingStrategy
    comparison_method: ComparisonMethod
    
    def validate(self) -> None:
        """Validate all configuration parameters."""
        if self.iterations <= 0:
            raise ValueError(f"Iterations must be positive, got {self.iterations}")
        if self.batch_size <= 0 or self.batch_size > self.iterations:
            raise ValueError(f"Invalid batch size: {self.batch_size}")


@dataclass
class SimulationMetrics:
    """Comprehensive metrics for simulation results."""
    total_battles: int = 0
    attacker_total_wins: int = 0
    defender_total_wins: int = 0
    execution_time_seconds: float = 0.0
    average_battle_time_ms: float = 0.0
    memory_usage_mb: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    
    @property
    def attacker_win_percentage(self) -> float:
        """Calculate attacker win percentage."""
        total = self.attacker_total_wins + self.defender_total_wins
        return (self.attacker_total_wins / total * 100) if total > 0 else 0.0
    
    @property
    def defender_win_percentage(self) -> float:
        """Calculate defender win percentage."""
        total = self.attacker_total_wins + self.defender_total_wins
        return (self.defender_total_wins / total * 100) if total > 0 else 0.0
    
    @property
    def battles_per_second(self) -> float:
        """Calculate battles per second throughput."""
        return self.total_battles / self.execution_time_seconds if self.execution_time_seconds > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize metrics to dictionary."""
        return {
            "total_battles": self.total_battles,
            "attacker_total_wins": self.attacker_total_wins,
            "defender_total_wins": self.defender_total_wins,
            "attacker_win_percentage": self.attacker_win_percentage,
            "defender_win_percentage": self.defender_win_percentage,
            "execution_time_seconds": self.execution_time_seconds,
            "average_battle_time_ms": self.average_battle_time_ms,
            "battles_per_second": self.battles_per_second,
            "memory_usage_mb": self.memory_usage_mb,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses
        }


@dataclass
class SimulationResult:
    """Complete result of simulation execution."""
    configuration: SimulationConfiguration
    metrics: SimulationMetrics
    battle_history: List[BattleResult] = field(default_factory=list)
    simulation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    
    def to_json(self) -> str:
        """Serialize complete result to JSON."""
        data = {
            "simulation_id": self.simulation_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "metrics": self.metrics.to_dict(),
            "battle_count": len(self.battle_history)
        }
        return json.dumps(data, indent=2)


class SimulationObserver(Protocol):
    """Protocol for simulation event observers."""
    
    def on_simulation_started(self, config: SimulationConfiguration) -> None:
        """Called when simulation starts."""
        ...
    
    def on_battle_completed(self, result: BattleResult) -> None:
        """Called when a battle is completed."""
        ...
    
    def on_batch_completed(self, batch_number: int, total_batches: int) -> None:
        """Called when a batch is completed."""
        ...
    
    def on_simulation_completed(self, result: SimulationResult) -> None:
        """Called when simulation completes."""
        ...
