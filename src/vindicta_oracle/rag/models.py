"""Domain models for the Oracle RAG utilization feature."""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, List
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class QueryType(str, Enum):
    """Types of queries supported by the RAG server."""
    UNIT_STATS = "unit_stats"
    WEAPON_PROFILE = "weapon_profile"
    ERRATA = "errata"
    META_CONTEXT = "meta_context"


class RetrievalMode(str, Enum):
    """The source of the retrieved data."""
    LIVE = "live"
    CACHED = "cached"
    PARTIAL = "partial"


class RAGQuery(BaseModel):
    """Structured search request issued to the MCP server."""
    unit_names: list[str] = Field(..., description="Unit names to search for")
    query_type: QueryType = Field(..., description="Type of query")
    version_filter: Optional[int] = Field(default=None, description="Optional minimum version")
    agent_id: str = Field(default="oracle", description="Identifier for the requesting system")


class RetrievedSegment(BaseModel):
    """A single result from the MCP tool response."""
    segment_id: UUID = Field(..., description="Maps to foundation RulesSegment.id")
    content_markdown: str = Field(..., description="Raw markdown rule text")
    relevance_score: float = Field(..., description="Distance/similarity (lower = more relevant)")
    version: int = Field(default=1, description="Version of this segment")
    url: str = Field(..., description="Source URL")
    retrieval_timestamp: datetime = Field(default_factory=datetime.now)


class UnitStats(BaseModel):
    """Structured extraction of numeric unit data from raw markdown."""
    name: str
    points_cost: int
    toughness: int
    wounds: int
    save: str
    weapons: list[str] = Field(default_factory=list)
    abilities: list[str] = Field(default_factory=list)
    source_segment_id: UUID


class RulesContextPackage(BaseModel):
    """Pre-assembled context distributed to debate agents."""
    segments: list[RetrievedSegment]
    unit_coverage: dict[str, bool]
    budget_total: int = Field(default=32000)
    budget_used: int = Field(default=0)  # Computed
    retrieval_mode: RetrievalMode


class GradingDataBundle(BaseModel):
    """Data bundle used by ListGrader for a single evaluation."""
    unit_data: dict[str, UnitStats]
    unresolved_units: list[str] = Field(default_factory=list)
    provenance: dict[str, UUID]
    retrieval_mode: RetrievalMode


class MetaSnapshot(BaseModel):
    """Aggregate meta statistics for a faction."""
    faction: str
    win_rate: Optional[float] = None
    popular_units: list[str] = Field(default_factory=list)
    meta_commentary: str = Field(default="")


class FallbackCacheEntry(BaseModel):
    """Internal cache row wrapper."""
    key: str
    segments: list[RetrievedSegment]
    cached_at: datetime = Field(default_factory=datetime.now)
    source_query: RAGQuery

