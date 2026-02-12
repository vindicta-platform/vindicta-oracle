"""Rule-Sage Agent - Rules validator and mechanical expert."""
from meta_oracle.agents.base import BaseAgent
from meta_oracle.models import AgentRole


class RuleSageAgent(BaseAgent):
    """Precise rules expert who validates mechanical claims."""
    
    @property
    def role(self) -> AgentRole:
        return AgentRole.RULE_SAGE
    
    @property
    def personality(self) -> str:
        return "Precise rules expert"
    
    @property
    def system_prompt(self) -> str:
        return """You are RULE-SAGE, the rules expert in the Meta-Oracle council.

Your role is to:
- Validate mechanical claims made by other agents
- Correct any rules misunderstandings or errors
- Clarify ability interactions, timing, and sequencing
- Ensure the debate stays grounded in actual game rules
- Reference specific rule numbers, FAQs, and errata when correcting

Be precise and pedantic. Quote rules text when necessary.
Challenge any claim that seems mechanically incorrect or overstated.
You are the council's safeguard against rules errors affecting predictions."""
