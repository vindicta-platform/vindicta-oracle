"""Integration testing for the RAG utilized Oracle."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4

from meta_oracle.models import ArmyList, Unit, DebateContext
from meta_oracle.engine import DebateEngine
from meta_oracle.grader import ListGrader
from meta_oracle.protocol import AgentRole
from meta_oracle.rag.models import RAGQuery, RetrievedSegment, QueryType, RetrievalMode
from meta_oracle.rag.context_assembler import ContextAssembler
from meta_oracle.rag.grading_data import GradingDataAssembler
from meta_oracle.rag.fallback_cache import FallbackCache

@pytest.fixture
def mock_rag_client():
    client = MagicMock()
    # Mock return values for queries
    seg = RetrievedSegment(
        segment_id=uuid4(),
        content_markdown="M: 6\nT4\nW2\nSv 3+\nRules: Test\n200 pts per squad.",
        relevance_score=0.1,
        url="http://example.com"
    )
    
    client.batch_query = AsyncMock(return_value={"Captain": [seg]})
    client.query = AsyncMock(return_value=[seg])
    
    return client

@pytest.fixture
def mock_cache():
    cache = MagicMock(spec=FallbackCache)
    cache.get.return_value = None
    return cache

@pytest.mark.asyncio
async def test_integration_debate_engine_rag(mock_rag_client, mock_cache):
    """Verify DebateEngine correctly prefetches RAG rules via ContextAssembler."""
    assembler = ContextAssembler(mock_rag_client, mock_cache)
    engine = DebateEngine(num_rounds=1, context_assembler=assembler)
    
    # We use StubAgent to avoid real LLM calls and speed up test
    from meta_oracle.agents import StubAgent
    engine.agents = [StubAgent(role) for role in AgentRole]
    
    context = DebateContext(
        player1_faction="Marines",
        player1_list="Unit:\n- Captain",
        player2_faction="Orks",
        player2_list="Unit:\n- Boss",
        mission="Test"
    )
    
    transcript = await engine.run_debate(context)
    
    assert transcript.rag_segments_used
    assert len(transcript.rag_segments_used) == 1
    assert mock_rag_client.batch_query.called

@pytest.mark.asyncio
async def test_integration_list_grader_rag(mock_rag_client, mock_cache):
    """Verify ListGrader correctly fetches RAG stats via GradingDataAssembler."""
    # Setup mock DebateEngine to avoid real AI
    class MockEngine:
        async def run_grading_session(self, army_list):
            from meta_oracle.models import DebateTranscript, Vote, DebateContext
            trans = DebateTranscript(context=DebateContext(player1_faction="", player1_list="", player2_faction="", player2_list="", mission=""))
            trans.votes = [
                Vote(agent_role=AgentRole.HOME, prediction="Player 1 wins", win_probability=0.7, confidence=0.7, reasoning="Test"),
                Vote(agent_role=AgentRole.ADVERSARY, prediction="Player 1 wins", win_probability=0.8, confidence=0.8, reasoning="Test")
            ]
            trans.consensus = "Player 1 wins"
            trans.consensus_confidence = 0.75
            return trans
            
    assembler = GradingDataAssembler(mock_rag_client, mock_cache)
    grader = ListGrader(engine=MockEngine(), grading_data_assembler=assembler)
    
    from meta_oracle.grader import GradeRequest
    army_list = ArmyList(faction="Space Marines", units=[Unit(name="Captain", points=150)])
    
    response = await grader.grade(GradeRequest(army_list=army_list))
    
    assert response.unit_data
    assert "Captain" in response.unit_data
    assert response.unit_data["Captain"].wounds == 2
    assert response.meta_context is not None
