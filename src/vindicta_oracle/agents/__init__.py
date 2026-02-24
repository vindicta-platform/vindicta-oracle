"""Meta-Oracle council agents and stubs."""
from meta_oracle.agents.base import BaseAgent
from meta_oracle.agents.home import HomeAgent
from meta_oracle.agents.adversary import AdversaryAgent
from meta_oracle.agents.arbiter import ArbiterAgent
from meta_oracle.agents.rule_sage import RuleSageAgent
from meta_oracle.agents.chaos import ChaosAgent
from meta_oracle.protocol import AgentRole, Argument, ArgumentType, OracleAgent, DebateRound
from meta_oracle.models import Vote

class StubAgent(OracleAgent):
    """A stub agent for testing that returns hardcoded responses."""

    def __init__(self, role: AgentRole) -> None:
        super().__init__(role)
        self.call_count = 0

    def analyze(self, context) -> str:
        """Return stub analysis."""
        self.call_count += 1
        return f"{self.role.value} analysis: stub response"

    def respond(self, transcript, round_num) -> Argument:
        """Return stub argument."""
        self.call_count += 1
        return Argument(
            agent_role=self.role,
            round=round_num,
            argument_type=ArgumentType.CLAIM,
            content=f"stub",
        )

    def vote(self, transcript) -> Vote:
        """Return stub vote."""
        self.call_count += 1
        return Vote(
            agent_role=self.role,
            prediction="Player 1 wins",
            win_probability=0.6,
            confidence=0.6,
            reasoning="stub"
        )

__all__ = [
    "BaseAgent",
    "HomeAgent",
    "AdversaryAgent",
    "ArbiterAgent",
    "RuleSageAgent",
    "ChaosAgent",
    "StubAgent",
]
