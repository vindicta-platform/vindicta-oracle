"""Unit tests for the FallbackCache."""

import pytest
from datetime import timedelta, datetime, timezone
import uuid

from meta_oracle.rag.models import RAGQuery, RetrievedSegment, QueryType
from meta_oracle.rag.fallback_cache import FallbackCache

@pytest.fixture
def tmp_cache(tmp_path):
    # Using diskcache in a temporary directory
    cache_dir = tmp_path / "rag_cache"
    cache = FallbackCache(str(cache_dir))
    yield cache
    cache.close()

def test_put_and_get(tmp_cache):
    """Test put() and get() round-trip with serialization."""
    query = RAGQuery(unit_names=["Space Marine"], query_type=QueryType.UNIT_STATS)
    segment = RetrievedSegment(
        segment_id=uuid.uuid4(),
        content_markdown="Toughness 4 Wounds 2",
        relevance_score=0.9,
        url="http://example.com/rules",
    )
    
    tmp_cache.put("space_marine", [segment], query)
    
    cached = tmp_cache.get("space_marine")
    assert cached is not None
    assert len(cached) == 1
    assert cached[0].content_markdown == "Toughness 4 Wounds 2"
    assert cached[0].segment_id == segment.segment_id

def test_cache_miss(tmp_cache):
    """Test get() returns None on cache miss."""
    assert tmp_cache.get("unknown_unit") is None

def test_is_stale(tmp_cache):
    """Test is_stale() with fresh and expired entries."""
    query = RAGQuery(unit_names=["Space Marine"], query_type=QueryType.UNIT_STATS)
    segment = RetrievedSegment(
        segment_id=uuid.uuid4(),
        content_markdown="Toughness 4 Wounds 2",
        relevance_score=0.9,
        url="http://example.com",
    )
    
    tmp_cache.put("stale_test", [segment], query)
    
    # Needs to be fresh (0 days old compared to 1 day limit)
    assert not tmp_cache.is_stale("stale_test", timedelta(days=1))
    
    # Test expiration by forcing age check (making max age negative)
    assert tmp_cache.is_stale("stale_test", timedelta(microseconds=-1))

def test_clear(tmp_cache):
    """Test clear() removes all entries."""
    query = RAGQuery(unit_names=["Test"], query_type=QueryType.UNIT_STATS)
    segment = RetrievedSegment(
        segment_id=uuid.uuid4(),
        content_markdown="Text",
        relevance_score=1.0,
        url="http://test.com",
    )
    
    tmp_cache.put("item1", [segment], query)
    tmp_cache.put("item2", [segment], query)
    
    assert tmp_cache.get("item1") is not None
    assert tmp_cache.get("item2") is not None
    
    tmp_cache.clear()
    
    assert tmp_cache.get("item1") is None
    assert tmp_cache.get("item2") is None
