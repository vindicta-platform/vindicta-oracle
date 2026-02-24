"""Disk-backed fallback cache for RAG rules."""

import os
import shutil
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional

import diskcache

from meta_oracle.rag.models import FallbackCacheEntry, RAGQuery, RetrievedSegment

logger = logging.getLogger(__name__)


class FallbackCache:
    """Stores the latest successful RAG retrieval per unit/topic."""

    def __init__(self, cache_dir: str = ".rag_cache"):
        os.makedirs(cache_dir, exist_ok=True)
        self.cache_dir = cache_dir
        self._cache = diskcache.Cache(cache_dir)

    def get(self, key: str) -> Optional[List[RetrievedSegment]]:
        """Retrieve cached segments by unit/topic key."""
        entry_data = self._cache.get(key)
        if not entry_data:
            return None

        try:
            # Using model_validate_json if we stored JSON, or raw dicts if stored dict
            entry = FallbackCacheEntry.model_validate_json(entry_data)
            return entry.segments
        except Exception as e:
            logger.error("Failed to parse fallback cache entry for key %s: %s", key, e)
            return None

    def put(self, key: str, segments: List[RetrievedSegment], source_query: RAGQuery) -> None:
        """Store or overwrite segments with timestamp."""
        entry = FallbackCacheEntry(
            key=key,
            segments=segments,
            source_query=source_query
        )
        try:
            # Store as JSON to ensure safe cross-process schema validation
            self._cache.set(key, entry.model_dump_json())
        except Exception as e:
            logger.error("Failed to write fallback cache for key %s: %s", key, e)

    def is_stale(self, key: str, max_age: timedelta) -> bool:
        """Check if cached data exceeds staleness threshold."""
        entry_data = self._cache.get(key)
        if not entry_data:
            return True

        try:
            entry = FallbackCacheEntry.model_validate_json(entry_data)
            now = datetime.now(timezone.utc)
            # Make entry's time aware
            entry_time = entry.cached_at
            if entry_time.tzinfo is None:
                entry_time = entry_time.replace(tzinfo=timezone.utc)

            delta = now - entry_time
            if delta > max_age:
                logger.warning("Cache data for %s is stale (age=%s)", key, delta)
                return True
            return False
        except Exception:
            return True

    def clear(self) -> None:
        """Purge all cached entries."""
        self._cache.clear()
        
    def close(self) -> None:
        """Close cache backends."""
        self._cache.close()
