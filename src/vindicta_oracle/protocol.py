"""Oracle Agent protocol - interface for all council agents."""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING, Optional, Protocol
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from vindicta_oracle.models import DebateTranscript as DebateTranscriptModel
    from vindicta_oracle.models import Vote

from vindicta_oracle.models import Argument as MetaArgument, DebateContext


class OracleAgent(Protocol):
    """Interface that all council agents must implement."""

    @property
    def role(self) -> str:
        """The agent's role identifier."""
        ...

    @property
    def personality(self) -> str:
        """Description of the agent's debate style."""
        ...

    def analyze(self, context: DebateContext) -> str:
        """Perform initial analysis of the matchup."""
        ...

    def respond(
        self, transcript: DebateTranscriptModel, round_num: int
    ) -> MetaArgument:
        """Generate a response based on debate history."""
        ...

    def vote(self, transcript: DebateTranscriptModel) -> Vote:
        """Cast final prediction vote after debate concludes."""
        ...


class AgentRole(str, Enum):
    """Roles in the Oracle Council."""

    HOME = "home"  # Advocate for player 1 / home faction
    ADVERSARY = "adversary"  # Advocate for player 2 / opponent
    ARBITER = "arbiter"  # Data-driven referee
    RULE_SAGE = "rule_sage"  # Rules expert / validation
    CHAOS = "chaos"  # Devil's advocate / upset detector


class ArgumentType(str, Enum):
    """Types of arguments in debate."""

    CLAIM = "claim"
    EVIDENCE = "evidence"
    REBUTTAL = "rebuttal"
    CONCESSION = "concession"
    QUESTION = "question"


class Argument(BaseModel):
    """A single argument in a debate."""

    id: UUID = Field(default_factory=uuid4)
    agent_role: AgentRole
    argument_type: ArgumentType
    content: str
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)
    references: list[str] = Field(default_factory=list)
    in_response_to: Optional[UUID] = None


class DebateRound(BaseModel):
    """A single round of debate."""

    round_number: int
    topic: str
    arguments: list[Argument] = Field(default_factory=list)

    def add_argument(self, argument: Argument) -> None:
        """Add an argument to this round."""
        self.arguments.append(argument)


class BaseOracleAgent(ABC):
    """Abstract base class for Oracle Council agents.

    Each agent specializes in a different aspect of game analysis.
    """

    def __init__(self, role: AgentRole) -> None:
        self.role = role
        self.id = uuid4()

    @abstractmethod
    async def analyze(self, context: dict) -> str:
        """Analyze the current debate context.

        Args:
            context: Debate context including lists, history, etc.

        Returns:
            Initial analysis text.
        """
        pass

    @abstractmethod
    async def respond(self, previous_arguments: list[Argument], topic: str) -> Argument:
        """Respond to previous arguments.

        Args:
            previous_arguments: Arguments from other agents.
            topic: Current debate topic.

        Returns:
            This agent's argument.
        """
        pass

    @abstractmethod
    async def vote(self, transcript: DebateTranscriptModel) -> dict:
        """Vote on debate outcome.

        Args:
            transcript: Complete debate transcript.

        Returns:
            Vote with prediction and confidence.
        """
        pass


# Type alias for agent implementations
AgentFactory = type[BaseOracleAgent]
