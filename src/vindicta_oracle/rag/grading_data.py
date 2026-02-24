"""List Grader Data Assembler."""

import logging
import re
from typing import Optional, List, Dict
from uuid import UUID


from meta_oracle.rag.client import RAGClient, RAGServerUnreachableError
from meta_oracle.rag.fallback_cache import FallbackCache
from meta_oracle.rag.models import (
    GradingDataBundle,
    RetrievalMode,
    RetrievedSegment,
    UnitStats,
    MetaSnapshot,
    RAGQuery,
    QueryType
)

logger = logging.getLogger(__name__)


class GradingDataAssembler:
    """Assembles data bundles for List Grader evaluation."""

    def __init__(self, client: RAGClient, cache: FallbackCache):
        self.client = client
        self.cache = cache

    async def fetch_unit_data(self, army_list: "meta_oracle.models.ArmyList") -> GradingDataBundle:
        """Fetch unit stats and costs from RAG."""
        unit_data: Dict[str, UnitStats] = {}
        unresolved_units: List[str] = []
        provenance: Dict[str, UUID] = {}
        mode = RetrievalMode.LIVE

        queries = [
            RAGQuery(
                unit_names=[u.name for u in army_list.units],
                query_type=QueryType.UNIT_STATS,
                agent_id="oracle_list_grader"
            )
        ]

        try:
            results = await self.client.batch_query(queries)
            for unit in army_list.units:
                name = unit.name
                segments = results.get(name, [])
                if not segments:
                    # RAG server returned no data for this unit
                    unresolved_units.append(name)
                    continue

                # Take the most relevant latest version segment
                latest_segments = {}
                for seg in segments:
                    seg_id = str(seg.segment_id)
                    if seg_id not in latest_segments or latest_segments[seg_id].version < seg.version:
                        latest_segments[seg_id] = seg
                
                sorted_segments = sorted(latest_segments.values(), key=lambda s: s.relevance_score)
                best_segment = sorted_segments[0]

                unit_stats = self._parse_unit_stats(best_segment, name)
                if unit_stats:
                    unit_data[name] = unit_stats
                    provenance[name] = best_segment.segment_id
                    self.cache.put(f"unit_data_{name}", [best_segment], queries[0])
                else:
                    unresolved_units.append(name)

        except RAGServerUnreachableError:
            logger.warning("RAG server unreachable, falling back to cache")
            mode = RetrievalMode.CACHED
            for unit in army_list.units:
                name = unit.name
                cached = self.cache.get(f"unit_data_{name}")
                if cached:
                    best_segment = sorted(cached, key=lambda s: s.relevance_score)[0]
                    stats = self._parse_unit_stats(best_segment, name)
                    if stats:
                        unit_data[name] = stats
                        provenance[name] = best_segment.segment_id
                    else:
                        unresolved_units.append(name)
                else:
                    unresolved_units.append(name)

        if unresolved_units:
            mode = RetrievalMode.PARTIAL
            if not unit_data:
                mode = RetrievalMode.CACHED  # Or maybe failed entirely.

        return GradingDataBundle(
            unit_data=unit_data,
            unresolved_units=unresolved_units,
            provenance=provenance,
            retrieval_mode=mode
        )

    async def fetch_meta_context(self, faction: str) -> Optional[MetaSnapshot]:
        """Fetch faction meta context from RAG."""
        try:
            query = RAGQuery(
                unit_names=[faction],
                query_type=QueryType.META_CONTEXT,
                agent_id="oracle_list_grader"
            )
            segments = await self.client.query(query)
            if segments:
                # Merge into MetaSnapshot...
                return MetaSnapshot(
                    faction=faction,
                    meta_commentary="\n".join(s.content_markdown for s in segments)
                )
        except RAGServerUnreachableError:
            logger.warning("Meta context unreachable")
        return None

    def _parse_unit_stats(self, segment: RetrievedSegment, default_name: str) -> Optional[UnitStats]:
        """Parse raw markdown into UnitStats."""
        # Simple heuristic extraction for MVP
        points = 0
        toughness = 4
        wounds = 2
        save = "3+"
        
        md = segment.content_markdown.lower()

        # Regex heuristics for stats
        t_match = re.search(r't(\d+)', md)
        if t_match:
            toughness = int(t_match.group(1))

        w_match = re.search(r'w(\d+)', md)
        if w_match:
            wounds = int(w_match.group(1))

        sv_match = re.search(r'sv\s*(\d+\+)', md)
        if sv_match:
            save = sv_match.group(1)

        pts_match = re.search(r'(\d+)\s*pts', md)
        if pts_match:
            points = int(pts_match.group(1))

        return UnitStats(
            name=default_name,
            points_cost=points,
            toughness=toughness,
            wounds=wounds,
            save=save,
            source_segment_id=segment.segment_id
        )
