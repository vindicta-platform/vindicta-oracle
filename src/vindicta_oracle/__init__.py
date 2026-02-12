"""Meta-Oracle: AI Council for competitive Warhammer predictions."""
from meta_oracle.models import (
    AgentRole,
    Argument,
    ArgumentType,
    DebateContext,
    DebateTranscript,
    Vote,
)
from meta_oracle.engine import DebateEngine
from meta_oracle.ollama_client import OllamaClient, OllamaConfig

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
