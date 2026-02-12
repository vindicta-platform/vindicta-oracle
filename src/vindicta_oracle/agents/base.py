"""Base agent class with shared Ollama integration."""
import re
from abc import ABC, abstractmethod

from meta_oracle.models import (
    AgentRole,
    Argument,
    ArgumentType,
    DebateContext,
    DebateTranscript,
    Vote,
)
from meta_oracle.ollama_client import OllamaClient


class BaseAgent(ABC):
    """Abstract base class for all council agents."""
    
    def __init__(self, client: OllamaClient | None = None):
        self.client = client or OllamaClient()
    
    @property
    @abstractmethod
    def role(self) -> AgentRole:
        """The agent's role in the council."""
        ...
    
    @property
    @abstractmethod
    def personality(self) -> str:
        """Description of the agent's debate style."""
        ...
    
    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """System prompt defining the agent's behavior."""
        ...
    
    def analyze(self, context: DebateContext) -> str:
        """Perform initial analysis of the matchup."""
        prompt = f"""Analyze this Warhammer 40K matchup:

Player 1: {context.player1_faction}
List: {context.player1_list}

Player 2: {context.player2_faction}
List: {context.player2_list}

Mission: {context.mission or "Standard"}
Terrain: {context.terrain or "Mixed"}

Provide your initial analysis based on your role. Be specific about units and tactics."""
        return self.client.generate(self.system_prompt, prompt)
    
    def respond(self, transcript: DebateTranscript, round_num: int) -> Argument:
        """Generate a response based on debate history."""
        history = self._format_history(transcript, round_num)
        context = transcript.context
        
        prompt = f"""Round {round_num} of the council debate.

MATCHUP:
- Player 1: {context.player1_faction}
- Player 2: {context.player2_faction}
- Mission: {context.mission or "Standard"}

Previous arguments this debate:
{history}

Now speak according to your role. Be specific about units, abilities, and tactical implications.
Keep your response focused and under 200 words."""
        
        content = self.client.generate(self.system_prompt, prompt)
        return Argument(
            agent_role=self.role,
            round=round_num,
            argument_type=ArgumentType.CLAIM,
            content=content,
        )
    
    def vote(self, transcript: DebateTranscript) -> Vote:
        """Cast final prediction vote after debate."""
        summary = self._format_full_debate(transcript)
        context = transcript.context
        
        prompt = f"""The council debate has concluded.

MATCHUP: {context.player1_faction} vs {context.player2_faction}

Full debate transcript:
{summary}

Now cast your final vote.

You MUST respond in this EXACT format:
WINNER: [Player 1 or Player 2 or Draw]
PROBABILITY: [number between 0 and 100]%
REASONING: [your reasoning in 2-3 sentences]"""
        
        response = self.client.generate(self.system_prompt, prompt)
        return self._parse_vote(response)
    
    def _format_history(self, transcript: DebateTranscript, round_num: int) -> str:
        """Format debate history up to current round."""
        lines = []
        for round_args in transcript.rounds[:round_num]:
            for arg in round_args:
                role_name = arg.agent_role.value.upper().replace("_", "-")
                lines.append(f"[{role_name}]: {arg.content}")
        return "\n\n".join(lines) if lines else "No arguments yet - you are opening the debate."
    
    def _format_full_debate(self, transcript: DebateTranscript) -> str:
        """Format the complete debate transcript."""
        return self._format_history(transcript, len(transcript.rounds) + 1)
    
    def _parse_vote(self, response: str) -> Vote:
        """Parse vote from LLM response."""
        # Determine prediction
        response_lower = response.lower()
        if "player 2" in response_lower:
            prediction = "Player 2 wins"
        elif "draw" in response_lower:
            prediction = "Draw"
        else:
            prediction = "Player 1 wins"
        
        # Extract probability
        probability = 0.5
        prob_match = re.search(r'(\d+)%', response)
        if prob_match:
            probability = int(prob_match.group(1)) / 100
            probability = max(0.0, min(1.0, probability))
        
        return Vote(
            agent_role=self.role,
            prediction=prediction,
            win_probability=probability,
            confidence=0.7,
            reasoning=response,
        )
