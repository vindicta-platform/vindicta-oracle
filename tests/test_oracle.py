"""
Unit tests for Meta-Oracle.
"""

import pytest
from meta_oracle.protocol import AgentRole, Argument, ArgumentType, DebateRound
from meta_oracle.transcript import DebateTranscript, Prediction, AgentVote
from meta_oracle.engine import DebateEngine
from meta_oracle.agents import StubAgent


class TestProtocol:
    """Tests for OracleAgent protocol."""

    def test_agent_roles(self):
        """All 5 agent roles should exist."""
        roles = list(AgentRole)
        assert len(roles) == 5
        assert AgentRole.HOME in roles
        assert AgentRole.ADVERSARY in roles
        assert AgentRole.ARBITER in roles
        assert AgentRole.RULE_SAGE in roles
        assert AgentRole.CHAOS in roles

    def test_argument_creation(self):
        """Argument should be creatable."""
        arg = Argument(
            agent_role=AgentRole.HOME,
            argument_type=ArgumentType.CLAIM,
            content="Player 1 will win"
        )
        
        assert arg.agent_role == AgentRole.HOME
        assert arg.content == "Player 1 will win"

    def test_debate_round(self):
        """DebateRound should hold arguments."""
        round = DebateRound(round_number=1, topic="Test")
        
        arg = Argument(
            agent_role=AgentRole.HOME,
            argument_type=ArgumentType.CLAIM,
            content="Test"
        )
        round.add_argument(arg)
        
        assert len(round.arguments) == 1


class TestTranscript:
    """Tests for DebateTranscript."""

    def test_transcript_creation(self):
        """Transcript should be creatable."""
        transcript = DebateTranscript(
            topic="Who will win?",
            player1_faction="Space Marines",
            player2_faction="Orks"
        )
        
        assert transcript.player1_faction == "Space Marines"

    def test_consensus_calculation(self):
        """Consensus should be calculated from votes."""
        transcript = DebateTranscript(
            topic="Test",
            player1_faction="A",
            player2_faction="B"
        )
        
        # 3 votes for player 1, 2 for player 2
        for i in range(3):
            transcript.add_vote(AgentVote(
                agent_role=AgentRole.HOME,
                prediction=Prediction(winner=1, confidence=0.7, reasoning="Test")
            ))
        for i in range(2):
            transcript.add_vote(AgentVote(
                agent_role=AgentRole.ADVERSARY,
                prediction=Prediction(winner=2, confidence=0.6, reasoning="Test")
            ))
        
        consensus = transcript.calculate_consensus()
        
        assert consensus.winner == 1

    def test_json_round_trip(self):
        """Transcript should serialize/deserialize."""
        transcript = DebateTranscript(
            topic="Test",
            player1_faction="A",
            player2_faction="B"
        )
        
        json_str = transcript.to_json()
        restored = DebateTranscript.from_json(json_str)
        
        assert restored.topic == "Test"


class TestDebateEngine:
    """Tests for DebateEngine."""

    @pytest.mark.asyncio
    async def test_engine_runs_debate(self):
        """Engine should run complete debate."""
        engine = DebateEngine(rounds=2)
        
        # Register stub agents
        for role in AgentRole:
            engine.register_agent(StubAgent(role))
        
        transcript = await engine.run_debate(
            topic="Who will win?",
            player1_faction="Marines",
            player2_faction="Orks"
        )
        
        assert len(transcript.rounds) == 2
        assert transcript.consensus is not None

    @pytest.mark.asyncio
    async def test_engine_collects_votes(self):
        """Engine should collect votes from all agents."""
        engine = DebateEngine(rounds=1)
        
        for role in AgentRole:
            engine.register_agent(StubAgent(role))
        
        transcript = await engine.run_debate(
            topic="Test",
            player1_faction="A",
            player2_faction="B"
        )
        
        assert len(transcript.votes) == 5  # All 5 agents voted
