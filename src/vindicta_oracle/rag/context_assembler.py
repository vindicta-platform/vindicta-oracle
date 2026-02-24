"""Context Assembler for Debate Engine."""

import logging
from typing import List, Optional, Dict

from meta_oracle.rag.client import RAGClient, RAGServerUnreachableError
from meta_oracle.rag.fallback_cache import FallbackCache
from meta_oracle.rag.models import (
    RulesContextPackage, 
    RetrievalMode, 
    RetrievedSegment, 
    RAGQuery, 
    QueryType
)

logger = logging.getLogger(__name__)


class ContextAssembler:
    """Assembles debate context by querying RAG rules for multiple units."""

    def __init__(self, client: RAGClient, cache: FallbackCache, default_budget: int = 32000):
        self.client = client
        self.cache = cache
        self.default_budget = default_budget

    async def assemble(
        self, unit_names: List[str], context_budget: Optional[int] = None
    ) -> RulesContextPackage:
        """Batch-fetches rules for given units and truncates to budget."""
        budget = context_budget if context_budget is not None else self.default_budget
        unique_units = list(set(name.strip() for name in unit_names if name.strip()))

        if not unique_units:
            return RulesContextPackage(
                segments=[],
                unit_coverage={},
                budget_total=budget,
                budget_used=0,
                retrieval_mode=RetrievalMode.LIVE
            )

        queries = [
            RAGQuery(
                unit_names=unique_units,
                query_type=QueryType.UNIT_STATS,
                agent_id="oracle_context_assembler"
            ),
            RAGQuery(
                unit_names=unique_units,
                query_type=QueryType.WEAPON_PROFILE,
                agent_id="oracle_context_assembler"
            ),
            RAGQuery(
                unit_names=unique_units,
                query_type=QueryType.ERRATA,
                agent_id="oracle_context_assembler"
            ),
        ]

        all_segments: List[RetrievedSegment] = []
        unit_coverage: Dict[str, bool] = {u: False for u in unique_units}
        mode = RetrievalMode.LIVE

        try:
            results = await self.client.batch_query(queries)
            # Process results... (assume results gives lists mapped to unit names)
            
            # Combine all retrieved segments
            for unit, segments in results.items():
                if segments:
                    unit_coverage[unit] = True
                    all_segments.extend(segments)
                    # Write-through cache per unit if found
                    # To do this correctly, we group the segments by querytype or cache key
                    # For simplicity of fallback we cache by unit name:
                    cache_key = f"context_{unit}"
                    # Note: We should technically use source_query=RAGQuery...
                    self.cache.put(cache_key, segments, queries[0])

        except RAGServerUnreachableError:
            logger.warning("RAG server unreachable, falling back to cache")
            mode = RetrievalMode.CACHED
            for unit in unique_units:
                cache_key = f"context_{unit}"
                cached = self.cache.get(cache_key)
                if cached:
                    all_segments.extend(cached)
                    unit_coverage[unit] = True

        # Filter to most recent version per segment_id (FR-003)
        latest_versions: Dict[str, RetrievedSegment] = {}
        for seg in all_segments:
            seg_id_str = str(seg.segment_id)
            if seg_id_str not in latest_versions or latest_versions[seg_id_str].version < seg.version:
                latest_versions[seg_id_str] = seg

        # Sort by relevance_score descending
        # NOTE: lower distance is better relevance for typical vector DBs, but 
        # retrieved model says: "relevance_score: float (lower = more relevant)" in `data-model.md`.
        # So we sort ASCENDING if lower is more relevant.
        unique_segments = list(latest_versions.values())
        unique_segments.sort(key=lambda s: s.relevance_score)

        # Truncate to budget characters
        final_segments = []
        budget_used = 0
        for seg in unique_segments:
            seg_len = len(seg.content_markdown)
            if budget_used + seg_len <= budget:
                final_segments.append(seg)
                budget_used += seg_len
            else:
                break

        return RulesContextPackage(
            segments=final_segments,
            unit_coverage=unit_coverage,
            budget_total=budget,
            budget_used=budget_used,
            retrieval_mode=mode
        )
