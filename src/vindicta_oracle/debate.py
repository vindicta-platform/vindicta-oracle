"""
DebateEngine for Meta-Oracle structured debates.

Orchestrates multi-agent debates per Issue #2.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class DebateRole(str, Enum):
    """Roles in a structured debate."""
    PROPOSER = "proposer"
    CHALLENGER = "challenger" 
    ARBITER = "arbiter"


@dataclass
class DebateTurn:
    """A single turn in a debate."""
    turn_number: int
    role: DebateRole
    agent_id: str
    argument: str
    confidence: float = 0.5
    references: list[str] = field(default_factory=list)


@dataclass
class DebateResult:
    """Final result of a debate."""
    winner: Optional[DebateRole] = None
    final_position: str = ""
    confidence: float = 0.0
    turns: list[DebateTurn] = field(default_factory=list)
    reasoning: str = ""


class DebateEngine(ABC):
    """Abstract interface for debate orchestration."""
    
    @abstractmethod
    async def start_debate(self, topic: str) -> str:
        """Start a new debate, returns debate_id."""
        pass
    
    @abstractmethod
    async def submit_turn(self, debate_id: str, turn: DebateTurn) -> None:
        """Submit a turn to the debate."""
        pass
    
    @abstractmethod
    async def resolve(self, debate_id: str) -> DebateResult:
        """Resolve the debate and return result."""
        pass
