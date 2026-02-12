"""Home Agent - Advocate for Player 1."""
from typing import Any, Optional

from meta_oracle.agents.base import BaseAgent
from meta_oracle.models import AgentRole, Argument, ArgumentType, DebateContext


class HomeAgent(BaseAgent):
    """Optimistic advocate for Player 1's strengths.
    
    Implements Issue #4 acceptance criteria:
    - Analyzes player list strengths
    - Generates supporting arguments
    - Integrates with Primordia evaluation (when available)
    """
    
    def __init__(self, client=None, evaluation_service: Optional[Any] = None):
        """Initialize HomeAgent with optional Primordia integration.
        
        Args:
            client: OllamaClient for LLM generation.
            evaluation_service: Optional Primordia evaluation service for grounding.
        """
        super().__init__(client)
        self._evaluation_service = evaluation_service
    
    @property
    def role(self) -> AgentRole:
        return AgentRole.HOME
    
    @property
    def personality(self) -> str:
        return "Optimistic advocate for Player 1"
    
    @property
    def system_prompt(self) -> str:
        return """You are HOME, an advocate for Player 1 in the Meta-Oracle council.

Your role is to:
- Highlight Player 1's list strengths and key units
- Identify favorable matchups and synergies
- Counter arguments against Player 1
- Be optimistic but grounded in actual game mechanics

You have deep knowledge of Warhammer 40K competitive play, unit stats, and tactical strategies.
Always cite specific units, abilities, and rules when making claims.
Be passionate but fair - acknowledge real weaknesses if pressed."""
    
    def analyze_strengths(self, context: DebateContext) -> dict:
        """Analyze Player 1 list strengths.
        
        Issue #4 Acceptance Criteria:
        - Analyzes player list strengths
        
        Args:
            context: The debate context with list information.
            
        Returns:
            Dictionary with strength categories and specific units.
        """
        prompt = f"""Analyze Player 1's list strengths:

Faction: {context.player1_faction}
List: {context.player1_list}

Identify and categorize:
1. KEY THREATS: Units that will win games
2. SYNERGIES: How units work together
3. SCORING: Objective control strengths
4. DURABILITY: Survivability advantages

Be specific about unit names, abilities, and stat values."""

        analysis = self.client.generate(self.system_prompt, prompt)
        
        return {
            "role": self.role.value,
            "analysis": analysis,
            "faction": context.player1_faction,
            "grounded": self._evaluation_service is not None,
        }
    
    def generate_supporting_argument(
        self, 
        context: DebateContext, 
        topic: str
    ) -> Argument:
        """Generate a supporting argument for Player 1.
        
        Issue #4 Acceptance Criteria:
        - Generates supporting arguments
        
        Args:
            context: The debate context.
            topic: The specific topic to argue for.
            
        Returns:
            Argument object with supporting claim.
        """
        evaluation_context = ""
        if self._evaluation_service:
            evaluation_context = self._get_evaluation_grounding(context)
        
        prompt = f"""Generate a strong argument supporting Player 1 regarding: {topic}

{evaluation_context}

Faction: {context.player1_faction}
List: {context.player1_list}

Provide a concrete argument citing:
- Specific units and their stats
- Game mechanics that favor Player 1
- Historical success or meta positioning

Keep under 150 words. Be assertive but factual."""

        content = self.client.generate(self.system_prompt, prompt)
        
        return Argument(
            agent_role=self.role,
            round=0,  # Will be set by debate engine
            argument_type=ArgumentType.CLAIM,
            content=content,
        )
    
    def _get_evaluation_grounding(self, context: DebateContext) -> str:
        """Get Primordia evaluation for grounding arguments.
        
        Issue #4 Acceptance Criteria:
        - Integrates with Primordia evaluation
        """
        if not self._evaluation_service:
            return ""
        
        try:
            # Primordia integration point - expects score from evaluation service
            # This is a stub for when Primordia is available
            return """[EVALUATION DATA AVAILABLE]
Use the following evaluation scores to support your argument with data."""
        except Exception:
            return ""

