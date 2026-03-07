"""Meta-Oracle: AI Council for competitive Warhammer predictions."""

from vindicta_oracle.models import (
    AgentRole,
    Argument,
    ArgumentType,
    DebateContext,
    DebateTranscript,
    Vote,
)
from vindicta_oracle.engine import DebateEngine
from vindicta_oracle.ollama_client import OllamaClient, OllamaConfig

__all__ = [
    "AgentRole",
    "Argument",
    "ArgumentType",
    "DebateContext",
    "DebateTranscript",
    "Vote",
    "DebateEngine",
    "OllamaClient",
    "OllamaConfig",
]

__version__ = "0.1.0"
