"""
Comprehensive unit tests for Meta-Oracle council agents.

Tests cover:
- Agent property definitions (role, personality, system_prompt)
- analyze() method functionality
- respond() method with debate history
- vote() parsing and format
- Edge cases and error handling
"""
import pytest
from unittest.mock import MagicMock, patch

from meta_oracle.models import (
    AgentRole,
    Argument,
    ArgumentType,
    DebateContext,
    DebateTranscript,
    Vote,
)
from meta_oracle.agents.base import BaseAgent
from meta_oracle.agents.home import HomeAgent
from meta_oracle.agents.adversary import AdversaryAgent
from meta_oracle.agents.arbiter import ArbiterAgent
from meta_oracle.agents.rule_sage import RuleSageAgent
from meta_oracle.agents.chaos import ChaosAgent


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_client():
    """Create a mock Ollama client."""
    client = MagicMock()
    client.generate = MagicMock(return_value="Test response")
    return client


@pytest.fixture
def sample_context():
    """Create a sample debate context."""
    return DebateContext(
        player1_faction="Space Marines",
        player1_list="Captain, 5x Intercessors, Redemptor Dreadnought",
        player2_faction="Orks",
        player2_list="Warboss, 20x Boyz, Battlewagon",
        mission="Take and Hold",
        terrain="Mixed ruins and forests"
    )


@pytest.fixture
def sample_transcript(sample_context):
    """Create a sample debate transcript with one round."""
    transcript = DebateTranscript(context=sample_context)
    transcript.rounds.append([
        Argument(
            agent_role=AgentRole.HOME,
            round=1,
            argument_type=ArgumentType.CLAIM,
            content="Space Marines have superior firepower."
        )
    ])
    return transcript


@pytest.fixture
def all_agents(mock_client):
    """Create all five council agents with mock client."""
    return [
        HomeAgent(mock_client),
        AdversaryAgent(mock_client),
        ArbiterAgent(mock_client),
        RuleSageAgent(mock_client),
        ChaosAgent(mock_client),
    ]


# =============================================================================
# Agent Property Tests
# =============================================================================

class TestAgentProperties:
    """Test that all agents define required properties correctly."""

    def test_home_agent_properties(self, mock_client):
        """HomeAgent should advocate for Player 1."""
        agent = HomeAgent(mock_client)
        assert agent.role == AgentRole.HOME
        assert "Player 1" in agent.system_prompt or "player 1" in agent.system_prompt.lower()
        assert len(agent.personality) > 0

    def test_adversary_agent_properties(self, mock_client):
        """AdversaryAgent should advocate for Player 2."""
        agent = AdversaryAgent(mock_client)
        assert agent.role == AgentRole.ADVERSARY
        assert "Player 2" in agent.system_prompt or "player 2" in agent.system_prompt.lower()
        assert len(agent.personality) > 0

    def test_arbiter_agent_properties(self, mock_client):
        """ArbiterAgent should be neutral and data-driven."""
        agent = ArbiterAgent(mock_client)
        assert agent.role == AgentRole.ARBITER
        assert "neutral" in agent.system_prompt.lower() or "data" in agent.system_prompt.lower()
        assert len(agent.personality) > 0

    def test_rule_sage_agent_properties(self, mock_client):
        """RuleSageAgent should focus on rules validation."""
        agent = RuleSageAgent(mock_client)
        assert agent.role == AgentRole.RULE_SAGE
        assert "rule" in agent.system_prompt.lower()
        assert len(agent.personality) > 0

    def test_chaos_agent_properties(self, mock_client):
        """ChaosAgent should be a devil's advocate."""
        agent = ChaosAgent(mock_client)
        assert agent.role == AgentRole.CHAOS
        assert len(agent.system_prompt) > 0
        assert len(agent.personality) > 0

    def test_all_agents_have_unique_roles(self, all_agents):
        """All five agents should have distinct roles."""
        roles = [agent.role for agent in all_agents]
        assert len(roles) == len(set(roles))

    def test_all_agents_have_system_prompts(self, all_agents):
        """All agents must have non-empty system prompts."""
        for agent in all_agents:
            assert len(agent.system_prompt) > 50, f"{agent.role} has short system prompt"


# =============================================================================
# Analyze Method Tests
# =============================================================================

class TestAnalyzeMethod:
    """Test the analyze() method across agents."""

    def test_analyze_calls_client(self, mock_client, sample_context):
        """analyze() should call the Ollama client."""
        agent = HomeAgent(mock_client)
        result = agent.analyze(sample_context)
        
        mock_client.generate.assert_called_once()
        call_args = mock_client.generate.call_args
        assert agent.system_prompt in call_args[0]
        assert "Space Marines" in call_args[0][1]

    def test_analyze_includes_all_context(self, mock_client, sample_context):
        """analyze() prompt should include all context fields."""
        agent = ArbiterAgent(mock_client)
        agent.analyze(sample_context)
        
        prompt = mock_client.generate.call_args[0][1]
        assert sample_context.player1_faction in prompt
        assert sample_context.player2_faction in prompt
        assert sample_context.mission in prompt

    def test_analyze_handles_none_fields(self, mock_client):
        """analyze() should handle None mission and terrain."""
        context = DebateContext(
            player1_faction="Tyranids",
            player1_list="Hive Tyrant",
            player2_faction="Necrons",
            player2_list="C'tan"
        )
        agent = HomeAgent(mock_client)
        agent.analyze(context)  # Should not raise


# =============================================================================
# Respond Method Tests
# =============================================================================

class TestRespondMethod:
    """Test the respond() method which generates arguments."""

    def test_respond_returns_argument(self, mock_client, sample_transcript):
        """respond() should return an Argument object."""
        agent = AdversaryAgent(mock_client)
        result = agent.respond(sample_transcript, round_num=2)
        
        assert isinstance(result, Argument)
        assert result.agent_role == AgentRole.ADVERSARY
        assert result.round == 2

    def test_respond_includes_history(self, mock_client, sample_transcript):
        """respond() should format debate history in prompt."""
        agent = ArbiterAgent(mock_client)
        agent.respond(sample_transcript, round_num=2)
        
        prompt = mock_client.generate.call_args[0][1]
        assert "HOME" in prompt  # Previous argument from HomeAgent
        assert "superior firepower" in prompt

    def test_respond_first_round(self, mock_client, sample_context):
        """respond() should work for opening round with no history."""
        transcript = DebateTranscript(context=sample_context)
        agent = HomeAgent(mock_client)
        
        result = agent.respond(transcript, round_num=1)
        
        assert result.round == 1
        prompt = mock_client.generate.call_args[0][1]
        assert "opening the debate" in prompt.lower() or "no arguments" in prompt.lower()


# =============================================================================
# Vote Method Tests
# =============================================================================

class TestVoteMethod:
    """Test the vote() method and response parsing."""

    def test_vote_returns_vote_object(self, mock_client, sample_transcript):
        """vote() should return a Vote object."""
        agent = HomeAgent(mock_client)
        result = agent.vote(sample_transcript)
        
        assert isinstance(result, Vote)
        assert result.agent_role == AgentRole.HOME

    def test_vote_parses_player1_winner(self, mock_client, sample_transcript):
        """vote() should correctly parse Player 1 as winner."""
        mock_client.generate.return_value = """
WINNER: Player 1
PROBABILITY: 65%
REASONING: Space Marines have the advantage.
"""
        agent = HomeAgent(mock_client)
        result = agent.vote(sample_transcript)
        
        assert "Player 1" in result.prediction
        assert result.win_probability == 0.65

    def test_vote_parses_player2_winner(self, mock_client, sample_transcript):
        """vote() should correctly parse Player 2 as winner."""
        mock_client.generate.return_value = """
WINNER: Player 2
PROBABILITY: 70%
REASONING: Orks will overwhelm.
"""
        agent = AdversaryAgent(mock_client)
        result = agent.vote(sample_transcript)
        
        assert "Player 2" in result.prediction
        assert result.win_probability == 0.70

    def test_vote_parses_draw(self, mock_client, sample_transcript):
        """vote() should correctly parse Draw prediction."""
        mock_client.generate.return_value = """
WINNER: Draw
PROBABILITY: 50%
REASONING: Evenly matched.
"""
        agent = ArbiterAgent(mock_client)
        result = agent.vote(sample_transcript)
        
        assert "Draw" in result.prediction
        assert result.win_probability == 0.50

    def test_vote_handles_malformed_response(self, mock_client, sample_transcript):
        """vote() should gracefully handle malformed LLM responses."""
        mock_client.generate.return_value = "I think player 1 might win maybe 60%"
        agent = HomeAgent(mock_client)
        result = agent.vote(sample_transcript)
        
        # Should still return a Vote, defaulting where needed
        assert isinstance(result, Vote)
        assert result.win_probability == 0.60

    def test_vote_clamps_probability(self, mock_client, sample_transcript):
        """vote() should clamp probability to 0.0-1.0 range."""
        mock_client.generate.return_value = "WINNER: Player 1\nPROBABILITY: 150%"
        agent = HomeAgent(mock_client)
        result = agent.vote(sample_transcript)
        
        assert result.win_probability <= 1.0


# =============================================================================
# Edge Cases
# =============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_agent_without_client_uses_default(self):
        """Agents should create default client if none provided."""
        with patch('meta_oracle.agents.base.OllamaClient') as MockClient:
            MockClient.return_value = MagicMock()
            agent = HomeAgent()
            assert agent.client is not None

    def test_empty_transcript_vote(self, mock_client, sample_context):
        """Agents should handle voting on empty transcripts."""
        transcript = DebateTranscript(context=sample_context)
        agent = RuleSageAgent(mock_client)
        
        result = agent.vote(transcript)
        assert isinstance(result, Vote)

    def test_long_debate_history(self, mock_client, sample_context):
        """Agents should handle long debate histories."""
        transcript = DebateTranscript(context=sample_context)
        
        # Add 5 rounds of 5 agents each
        for round_num in range(1, 6):
            round_args = []
            for role in AgentRole:
                round_args.append(Argument(
                    agent_role=role,
                    round=round_num,
                    argument_type=ArgumentType.CLAIM,
                    content=f"Argument from {role.value} in round {round_num}"
                ))
            transcript.rounds.append(round_args)
        
        agent = ChaosAgent(mock_client)
        result = agent.respond(transcript, round_num=6)
        
        assert isinstance(result, Argument)


# =============================================================================
# Integration Tests (mock client)
# =============================================================================

class TestAgentInteraction:
    """Test agents work together as expected."""

    def test_all_agents_can_analyze(self, all_agents, sample_context):
        """All agents should successfully analyze a context."""
        for agent in all_agents:
            result = agent.analyze(sample_context)
            assert isinstance(result, str)

    def test_all_agents_can_respond(self, all_agents, sample_transcript):
        """All agents should successfully respond in debate."""
        for agent in all_agents:
            result = agent.respond(sample_transcript, round_num=2)
            assert isinstance(result, Argument)
            assert result.agent_role == agent.role

    def test_all_agents_can_vote(self, all_agents, sample_transcript):
        """All agents should successfully cast votes."""
        for agent in all_agents:
            result = agent.vote(sample_transcript)
            assert isinstance(result, Vote)
            assert result.agent_role == agent.role
