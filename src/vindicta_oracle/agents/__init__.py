"""Meta-Oracle council agents and stubs."""
from meta_oracle.agents.base import BaseAgent
from meta_oracle.agents.home import HomeAgent
from meta_oracle.agents.adversary import AdversaryAgent
from meta_oracle.agents.arbiter import ArbiterAgent
from meta_oracle.agents.rule_sage import RuleSageAgent
from meta_oracle.agents.chaos import ChaosAgent
from meta_oracle.protocol import AgentRole, Argument, ArgumentType, OracleAgent, DebateRound

class StubAgent(OracleAgent):
    """A stub agent for testing that returns hardcoded responses."""
    
    def __init__(self, role: AgentRole) -> None:
        super().__init__(role)
        self.call_count = 0
    
    async def analyze(self, context: dict) -> str:
        """Return stub analysis."""
        self.call_count += 1
        return f"{self.role.value} analysis: stub response"
    
    async def respond(self, previous_arguments: list[Argument], topic: str) -> Argument:
        """Return stub argument."""
        self.call_count += 1
        return Argument(
            agent_role=self.role,
            argument_type=ArgumentType.CLAIM,
            content=f"{self.role.value} response to: {topic}",
            confidence=0.7
        )
    
    async def vote(self, transcript) -> dict:
        """Return stub vote."""
        self.call_count += 1
        # HOME votes for player 1, ADVERSARY for player 2, others random
        winner = 1 if self.role in [AgentRole.HOME, AgentRole.ARBITER] else 2
        return {
            "winner": winner,
            "confidence": 0.6,
            "reasoning": f"{self.role.value} votes for player {winner}",
            "upset": self.role == AgentRole.CHAOS
        }

__all__ = [
    "BaseAgent",
    "HomeAgent",
    "AdversaryAgent",
    "ArbiterAgent",
    "RuleSageAgent",
    "ChaosAgent",
    "StubAgent",
]
