"""
DebateTranscript for Meta-Oracle.

Records the complete history of a debate session.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from meta_oracle.protocol import AgentRole, Argument, DebateRound


class Prediction(BaseModel):
    """A prediction outcome with confidence."""
    
    winner: int  # 1 or 2
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    upset_detected: bool = False


class AgentVote(BaseModel):
    """An agent's vote on the outcome."""
    
    agent_role: AgentRole
    prediction: Prediction
    dissenting: bool = False


class DebateTranscript(BaseModel):
    """
    Complete record of a Meta-Oracle debate session.
    
    Captures all rounds, arguments, votes, and the final consensus.
    """
    
    id: UUID = Field(default_factory=uuid4)
    
    # Context
    topic: str
    player1_faction: str
    player2_faction: str
    
    # Debate content
    rounds: list[DebateRound] = Field(default_factory=list)
    
    # Votes and outcome
    votes: list[AgentVote] = Field(default_factory=list)
    consensus: Optional[Prediction] = None
    
    # Timing
    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None
    
    def add_round(self, round: DebateRound) -> None:
        """Add a debate round."""
        self.rounds.append(round)
    
    def add_vote(self, vote: AgentVote) -> None:
        """Add an agent vote."""
        self.votes.append(vote)
    
    def calculate_consensus(self) -> Prediction:
        """Calculate consensus from votes."""
        if not self.votes:
            return Prediction(winner=1, confidence=0.5, reasoning="No votes")
        
        # Count votes
        winner_votes = {}
        total_confidence = 0
        
        for vote in self.votes:
            w = vote.prediction.winner
            winner_votes[w] = winner_votes.get(w, 0) + 1
            total_confidence += vote.prediction.confidence
        
        # Find majority
        winner = max(winner_votes, key=winner_votes.get)
        confidence = total_confidence / len(self.votes)
        
        # Check for upset
        upset = any(v.prediction.upset_detected for v in self.votes)
        
        self.consensus = Prediction(
            winner=winner,
            confidence=confidence,
            reasoning=f"Consensus from {len(self.votes)} agents",
            upset_detected=upset
        )
        return self.consensus
    
    def to_json(self) -> str:
        """Serialize to JSON."""
        return self.model_dump_json(indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> "DebateTranscript":
        """Deserialize from JSON."""
        return cls.model_validate_json(json_str)
