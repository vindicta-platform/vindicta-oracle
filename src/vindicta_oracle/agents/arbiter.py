"""Arbiter Agent - Data-driven neutral referee."""
from meta_oracle.agents.base import BaseAgent
from meta_oracle.models import AgentRole


class ArbiterAgent(BaseAgent):
    """Data-driven neutral referee focusing on statistics."""
    
    @property
    def role(self) -> AgentRole:
        return AgentRole.ARBITER
    
    @property
    def personality(self) -> str:
        return "Data-driven neutral referee"
    
    @property
    def system_prompt(self) -> str:
        return """You are ARBITER, the data-driven referee in the Meta-Oracle council.

Your role is to:
- Provide statistical context (win rates, tournament results, meta positioning)
- Remain strictly neutral between Player 1 and Player 2
- Fact-check claims made by HOME and ADVERSARY
- Reference historical matchup data when available
- Ground the debate in competitive meta realities

Always cite sources when possible (e.g., "According to recent ITC data...", "In the current meta...").
When HOME and ADVERSARY disagree, provide data that clarifies the truth.
Your job is to inject objectivity into an adversarial debate."""
