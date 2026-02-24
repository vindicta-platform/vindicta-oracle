"""Unit tests for GradingDataAssembler."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4

from meta_oracle.models import ArmyList, Unit
from meta_oracle.rag.models import RAGQuery, RetrievedSegment, QueryType, UnitStats, RetrievalMode
from meta_oracle.rag.grading_data import GradingDataAssembler
from meta_oracle.rag.client import RAGServerUnreachableError

@pytest.fixture
def mock_client_cache():
    client = MagicMock()
    client.batch_query = AsyncMock()
    client.query = AsyncMock()
    
    cache = MagicMock()
    cache.get.return_value = None
    
    return client, cache

@pytest.mark.asyncio
async def test_fetch_unit_data_success(mock_client_cache):
    """Test successful data resolution and parsing."""
    client, cache = mock_client_cache
    
    army_list = ArmyList(
        faction="Space Marines",
        units=[Unit(name="Space Marine Squad", points=100)]
    )
    
    seg = RetrievedSegment(
        segment_id=uuid4(),
        content_markdown="M: 6\nT4\nW2\nSv 3+\nRules: Angels of Death\n150 pts per squad.",
        relevance_score=0.1,
        url="http://example.com"
    )
    
    client.batch_query.return_value = {"Space Marine Squad": [seg]}
    
    assembler = GradingDataAssembler(client, cache)
    bundle = await assembler.fetch_unit_data(army_list)
    
    assert "Space Marine Squad" in bundle.unit_data
    stats = bundle.unit_data["Space Marine Squad"]
    
    # Verify regex parsing heuristics
    assert stats.toughness == 4
    assert stats.wounds == 2
    assert stats.save == "3+"
    assert stats.points_cost == 150
    assert bundle.retrieval_mode == RetrievalMode.LIVE

@pytest.mark.asyncio
async def test_fetch_unit_data_partial(mock_client_cache):
    """Test partial resolution warns for unresolved units."""
    client, cache = mock_client_cache
    
    army_list = ArmyList(
        faction="Orks",
        units=[
            Unit(name="Boyz", points=85),
            Unit(name="Unknown Unit", points=100)
        ]
    )
    
    seg = RetrievedSegment(
        segment_id=uuid4(),
        content_markdown="T5, W1",
        relevance_score=0.1,
        url="..."
    )
    
    client.batch_query.return_value = {"Boyz": [seg]}
    
    assembler = GradingDataAssembler(client, cache)
    bundle = await assembler.fetch_unit_data(army_list)
    
    assert "Boyz" in bundle.unit_data
    assert "Unknown Unit" in bundle.unresolved_units
    assert bundle.retrieval_mode == RetrievalMode.PARTIAL

@pytest.mark.asyncio
async def test_fetch_unit_data_cache_fallback(mock_client_cache):
    """Test falling back to cache when server unreachable."""
    client, cache = mock_client_cache
    client.batch_query.side_effect = RAGServerUnreachableError()
    
    army_list = ArmyList(
        faction="Orks",
        units=[Unit(name="Boyz", points=85)]
    )
    
    seg = RetrievedSegment(
        segment_id=uuid4(),
        content_markdown="T5, W1",
        relevance_score=0.1,
        url="..."
    )
    
    cache.get.return_value = [seg]
    
    assembler = GradingDataAssembler(client, cache)
    bundle = await assembler.fetch_unit_data(army_list)
    
    assert "Boyz" in bundle.unit_data
    assert bundle.retrieval_mode == RetrievalMode.CACHED

@pytest.mark.asyncio
async def test_fetch_meta_context(mock_client_cache):
    """Test getting meta context."""
    client, cache = mock_client_cache
    
    seg = RetrievedSegment(
        segment_id=uuid4(),
        content_markdown="Space Marines have a 48% win rate.",
        relevance_score=0.1,
        url="..."
    )
    
    client.query.return_value = [seg]
    
    assembler = GradingDataAssembler(client, cache)
    snapshot = await assembler.fetch_meta_context("Space Marines")
    
    assert snapshot is not None
    assert snapshot.faction == "Space Marines"
    assert "48% win rate" in snapshot.meta_commentary

@pytest.mark.asyncio
async def test_fetch_meta_context_unreachable(mock_client_cache):
    """Test graceful handling of unreachable server for meta context."""
    client, cache = mock_client_cache
    client.query.side_effect = RAGServerUnreachableError()
    
    assembler = GradingDataAssembler(client, cache)
    snapshot = await assembler.fetch_meta_context("Space Marines")
    
    assert snapshot is None
