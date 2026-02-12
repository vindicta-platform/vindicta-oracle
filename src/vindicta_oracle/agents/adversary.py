"""Adversary Agent - Advocate for Player 2."""
from typing import Optional

from meta_oracle.agents.base import BaseAgent
from meta_oracle.models import AgentRole, Argument, ArgumentType, DebateContext


class AdversaryAgent(BaseAgent):
    """Skeptical advocate for Player 2's advantages.
    
    Implements Issue #5 acceptance criteria:
    - Identifies weaknesses in Player 1's list
    - Generates counter-arguments against HOME
    - Devil's advocate behavior to stress-test predictions
    """
    
    def __init__(self, client=None, aggression_level: int = 7):
        """Initialize AdversaryAgent with configurable aggression.
        
        Args:
            client: OllamaClient for LLM generation.
            aggression_level: 1-10 scale for how aggressively to counter (default 7).
        """
        super().__init__(client)
        self._aggression_level = min(10, max(1, aggression_level))
    
    @property
    def role(self) -> AgentRole:
        return AgentRole.ADVERSARY
    
    @property
    def personality(self) -> str:
        return "Skeptical advocate for Player 2"
    
    @property
    def system_prompt(self) -> str:
        return """You are ADVERSARY, an advocate for Player 2 in the Meta-Oracle council.

Your role is to:
- Highlight Player 2's list strengths and key threats
- Counter claims made about Player 1's advantages
- Identify Player 1's weaknesses and exploitable gaps
- Challenge optimistic assessments with tactical reality

Be thorough and analytical. Cite specific counters, stat comparisons, and tactical scenarios.
Push back against HOME's optimism with concrete counterpoints.
You want Player 2 to be taken seriously as a threat."""
    
    def identify_weaknesses(self, context: DebateContext) -> dict:
        """Identify weaknesses in Player 1's list.
        
        Issue #5 Acceptance Criteria:
        - Identifies weaknesses
        
        Args:
            context: The debate context with list information.
            
        Returns:
            Dictionary with weakness categories and exploits.
        """
        prompt = f"""Analyze Player 1's list WEAKNESSES:

Faction: {context.player1_faction}
List: {context.player1_list}

Player 2 Counters:
Faction: {context.player2_faction}
List: {context.player2_list}

Identify and categorize:
1. VULNERABILITIES: Gaps in defense or offense
2. BAD MATCHUPS: Where Player 2 dominates
3. EXPLOITABLE SYNERGIES: Dependencies that can be broken
4. SCORING WEAKNESSES: Objective control problems

Be specific about unit names, stat comparisons, and tactical exploits."""

        analysis = self.client.generate(self.system_prompt, prompt)
        
        return {
            "role": self.role.value,
            "analysis": analysis,
            "target_faction": context.player1_faction,
            "aggression_level": self._aggression_level,
        }
    
    def generate_counter_argument(
        self, 
        context: DebateContext, 
        claim_to_counter: str
    ) -> Argument:
        """Generate a counter-argument against a claim.
        
        Issue #5 Acceptance Criteria:
        - Generates counter-arguments
        
        Args:
            context: The debate context.
            claim_to_counter: The specific claim to argue against.
            
        Returns:
            Argument object with rebuttal.
        """
        aggression_modifier = self._get_aggression_modifier()
        
        prompt = f"""Counter this claim about Player 1:
CLAIM: "{claim_to_counter}"

{aggression_modifier}

Context:
- Player 1: {context.player1_faction}
- Player 2: {context.player2_faction}

Provide a concrete counter-argument citing:
- Specific unit counters from Player 2's list
- Stat comparisons that favor Player 2
- Tactical scenarios where the claim fails

Keep under 150 words. Be factual but assertive."""

        content = self.client.generate(self.system_prompt, prompt)
        
        return Argument(
            agent_role=self.role,
            round=0,  # Will be set by debate engine
            argument_type=ArgumentType.REBUTTAL,
            content=content,
        )
    
    def devils_advocate(self, context: DebateContext, consensus: str) -> Argument:
        """Challenge a consensus prediction as devil's advocate.
        
        Issue #5 Acceptance Criteria:
        - Devil's advocate behavior
        
        Args:
            context: The debate context.
            consensus: The current consensus prediction to challenge.
            
        Returns:
            Argument challenging the consensus.
        """
        prompt = f"""As devil's advocate, challenge this consensus prediction:
CONSENSUS: "{consensus}"

You MUST argue the opposite position, even if unlikely.

Matchup:
- Player 1: {context.player1_faction}
- Player 2: {context.player2_faction}

Provide:
1. The strongest possible counter-case
2. Scenarios where consensus is wrong
3. Edge cases or lucky swings that could flip the outcome

Be provocative but grounded in real game mechanics."""

        content = self.client.generate(self.system_prompt, prompt)
        
        return Argument(
            agent_role=self.role,
            round=0,
            argument_type=ArgumentType.CHALLENGE,
            content=content,
        )
    
    def _get_aggression_modifier(self) -> str:
        """Get prompt modifier based on aggression level."""
        if self._aggression_level >= 8:
            return "Be AGGRESSIVE. Show no mercy to weak arguments. Demolish their claims."
        elif self._aggression_level >= 5:
            return "Be firm and assertive. Challenge assumptions directly."
        else:
            return "Be measured but thorough. Present alternatives calmly."

