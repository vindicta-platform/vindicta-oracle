"""Unit tests for the RAGClient."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4

from meta_oracle.rag.models import RAGQuery, QueryType, RetrievedSegment
from meta_oracle.rag.client import RAGClient, RAGServerUnreachableError

@pytest.fixture
def mock_mcp_client():
    with patch("meta_oracle.rag.client.ClientSession") as mock_session_cls:
        with patch("meta_oracle.rag.client.sse_client") as mock_sse:
            with patch("meta_oracle.rag.client.AsyncExitStack") as mock_stack:
                # Setup mock async exit stack
                mock_stack_instance = AsyncMock()
                mock_stack.return_value = mock_stack_instance
                
                # Mock SSE streams
                mock_stream_pair = (MagicMock(), MagicMock())
                mock_stack_instance.enter_async_context.side_effect = [
                    mock_stream_pair,  # sse_client
                    AsyncMock()        # ClientSession
                ]
                
                session_instance = AsyncMock()
                
                # Mock call_tool response
                mock_response = MagicMock()
                mock_response.content = [
                    MagicMock(text='{"segments": [{"segment_id": "123e4567-e89b-12d3-a456-426614174000", "content_markdown": "Test Rules", "relevance_score": 0.9, "version": 1, "url": "http://test"}]}')
                ]
                session_instance.call_tool.return_value = mock_response
                
                yield session_instance

@pytest.mark.asyncio
async def test_rag_client_lifecycle(mock_mcp_client):
    """Test connect(), disconnect() and async context manager."""
    client = RAGClient("http://localhost:8000")
    
    # Test context manager
    with patch("meta_oracle.rag.client.ClientSession") as mock_cls:
        mock_cls.return_value = mock_mcp_client
        
        async with client as c:
            assert c._session is not None
        
        # After exit, session should be None
        assert client._session is None

@pytest.mark.asyncio
async def test_rag_client_query(mock_mcp_client):
    """Test query() sends correct tool name and arguments."""
    client = RAGClient("http://localhost:8000")
    client._session = mock_mcp_client  # Inject mock directly
    
    query = RAGQuery(unit_names=["Space Marine"], query_type=QueryType.UNIT_STATS)
    segments = await client.query(query)
    
    assert len(segments) == 1
    assert segments[0].content_markdown == "Test Rules"
    
    # Verify call_tool arguments
    mock_mcp_client.call_tool.assert_called_once()
    args, kwargs = mock_mcp_client.call_tool.call_args
    assert args[0] == "search_40k_rules"
    assert kwargs["arguments"]["unit_names"] == ["Space Marine"]
    assert kwargs["arguments"]["query_type"] == "unit_stats"

@pytest.mark.asyncio
async def test_rag_client_batch_query(mock_mcp_client):
    """Test batch_query() aggregates overlapping unit names."""
    client = RAGClient("http://localhost:8000")
    client._session = mock_mcp_client
    
    query1 = RAGQuery(unit_names=["Space Marine"], query_type=QueryType.UNIT_STATS)
    query2 = RAGQuery(unit_names=["Ork Boyz", "Space Marine"], query_type=QueryType.UNIT_STATS)
    
    results = await client.batch_query([query1, query2])
    
    # Verify single consolidated call
    mock_mcp_client.call_tool.assert_called_once()
    args, kwargs = mock_mcp_client.call_tool.call_args
    
    # Unit names should be deduped
    requested_units = set(kwargs["arguments"]["unit_names"])
    assert requested_units == {"Space Marine", "Ork Boyz"}
    
    assert "Space Marine" in results
    assert "Ork Boyz" in results

@pytest.mark.asyncio
async def test_rag_client_unreachable():
    """Test RAGServerUnreachableError is raised on connection failure."""
    client = RAGClient("http://invalid_address")
    
    with patch("meta_oracle.rag.client.sse_client", side_effect=Exception("Connection failed")):
        with pytest.raises(RAGServerUnreachableError):
            await client.connect()
