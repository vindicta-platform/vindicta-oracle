"""Unit tests for the ContextAssembler."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4

from meta_oracle.rag.models import RAGQuery, RetrievedSegment, QueryType, RulesContextPackage
from meta_oracle.rag.context_assembler import ContextAssembler
from meta_oracle.rag.client import RAGServerUnreachableError

@pytest.fixture
def mock_client_cache():
    client = MagicMock()
    # Mock async method
    client.batch_query = AsyncMock()
    
    # Mock fallback cache
    cache = MagicMock()
    cache.get.return_value = None
    
    return client, cache

@pytest.mark.asyncio
async def test_assemble_basic(mock_client_cache):
    """Test batch assembly."""
    client, cache = mock_client_cache
    
    seg1 = RetrievedSegment(
        segment_id=uuid4(),
        content_markdown="Space Marine stats...",
        relevance_score=0.9,
        version=1,
        url="http://example.com/marine"
    )
    
    # Mock returning one segment for Space Marine
    client.batch_query.return_value = {"Space Marine": [seg1]}
    
    assembler = ContextAssembler(client, cache, default_budget=1000)
    package = await assembler.assemble(["Space Marine"])
    
    assert len(package.segments) == 1
    assert package.unit_coverage["Space Marine"] is True
    assert package.budget_used > 0
    cache.put.assert_called()

@pytest.mark.asyncio
async def test_assemble_version_filtering(mock_client_cache):
    """Test version filtering — only latest version per segment retained."""
    client, cache = mock_client_cache
    
    seg_id = uuid4()
    seg_v1 = RetrievedSegment(
        segment_id=seg_id,
        content_markdown="Old Rules",
        relevance_score=0.9,
        version=1,
        url="http://example.com/marine"
    )
    seg_v2 = RetrievedSegment(
        segment_id=seg_id,
        content_markdown="New Rules",
        relevance_score=0.9,
        version=2,
        url="http://example.com/marine"
    )
    
    # Return both versions
    client.batch_query.return_value = {"Space Marine": [seg_v1, seg_v2]}
    
    assembler = ContextAssembler(client, cache, default_budget=1000)
    package = await assembler.assemble(["Space Marine"])
    
    assert len(package.segments) == 1
    assert package.segments[0].version == 2

@pytest.mark.asyncio
async def test_assemble_truncation(mock_client_cache):
    """Test relevance truncation when total content exceeds budget."""
    client, cache = mock_client_cache
    
    # Create two segments, each 100 characters long
    seg_better = RetrievedSegment(
        segment_id=uuid4(),
        content_markdown="A" * 100,
        relevance_score=0.1,  # better relevance (lower)
        url="http://test",
    )
    seg_worse = RetrievedSegment(
        segment_id=uuid4(),
        content_markdown="B" * 100,
        relevance_score=0.5,
        url="http://test",
    )
    
    client.batch_query.return_value = {"Space Marine": [seg_better, seg_worse]}
    
    # Set budget to 150 characters (only enough for one segment)
    assembler = ContextAssembler(client, cache, default_budget=150)
    package = await assembler.assemble(["Space Marine"])
    
    assert len(package.segments) == 1
    assert package.segments[0].content_markdown == "A" * 100

@pytest.mark.asyncio
async def test_assemble_server_unreachable(mock_client_cache):
    """Test fallback to cache on RAGServerUnreachableError."""
    client, cache = mock_client_cache
    client.batch_query.side_effect = RAGServerUnreachableError()
    
    cached_seg = RetrievedSegment(
        segment_id=uuid4(),
        content_markdown="Cached Rules",
        relevance_score=1.0,
        url="http://example.com"
    )
    
    # Make cache return a value
    cache.get.return_value = [cached_seg]
    
    assembler = ContextAssembler(client, cache, default_budget=1000)
    package = await assembler.assemble(["Space Marine"])
    
    assert len(package.segments) == 1
    assert package.retrieval_mode.value == "cached"
    assert package.segments[0].content_markdown == "Cached Rules"
