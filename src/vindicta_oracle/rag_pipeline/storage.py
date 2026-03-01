"""RAG Pipeline storage — ChromaDB + Ollama embeddings.

Implements embedded ChromaDB with SQLite persistence (FR-004),
local Ollama embeddings, and versioned upsert logic (FR-006).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Protocol

from vindicta_foundation.models.rag import RulesSegment
from vindicta_foundation.rag_pipeline.scraper import ScrapedChunk

logger = logging.getLogger(__name__)


class EmbeddingProvider(Protocol):
    """Protocol for embedding generation — enables testing without Ollama."""

    def embed(self, text: str) -> list[float]:
        """Generate an embedding vector for the given text."""
        ...


class VectorStore(Protocol):
    """Protocol for vector storage — enables testing without ChromaDB."""

    def upsert(
        self,
        ids: list[str],
        documents: list[str],
        metadatas: list[dict[str, Any]],
        embeddings: list[list[float]],
    ) -> None:
        """Upsert documents with embeddings and metadata."""
        ...

    def query(
        self,
        query_embeddings: list[list[float]],
        n_results: int = 5,
    ) -> dict[str, Any]:
        """Query the store by embedding similarity."""
        ...

    def get(
        self,
        ids: list[str] | None = None,
        where: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Get documents by ID or filter."""
        ...


class RulesStorage:
    """Storage layer for rules segments with embedding and versioning.

    Uses protocol-based dependency injection so ChromaDB and Ollama
    can be swapped with mocks for testing.
    """

    def __init__(
        self,
        store: VectorStore,
        embedder: EmbeddingProvider,
    ) -> None:
        self._store = store
        self._embedder = embedder

    def store_chunk(self, chunk: ScrapedChunk) -> RulesSegment:
        """Store a scraped chunk with embedding, handling dedup (FR-003).

        If a chunk with the same content_hash already exists, it is
        skipped. If the URL exists with different content, a new version
        is created (FR-006).

        Args:
            chunk: A scraped content chunk.

        Returns:
            The stored ``RulesSegment``.
        """
        # Check for existing content with same hash
        existing = self._find_by_hash(chunk.content_hash)
        if existing is not None:
            logger.info(
                "Skipping duplicate chunk (hash=%s) for %s",
                chunk.content_hash[:12],
                chunk.url,
            )
            return existing

        # Check for existing content at same URL (new version)
        version = self._get_next_version(chunk.url)

        # Generate embedding
        embedding = self._embedder.embed(chunk.content_markdown)

        # Create segment model
        segment = RulesSegment(
            url=chunk.url,  # type: ignore[arg-type]
            content_markdown=chunk.content_markdown,
            content_hash=chunk.content_hash,
            version=version,
            embedding=embedding,
            timestamp=datetime.now(timezone.utc),
        )

        # Upsert to vector store
        segment_id = str(segment.id)
        self._store.upsert(
            ids=[segment_id],
            documents=[chunk.content_markdown],
            metadatas=[
                {
                    "url": chunk.url,
                    "content_hash": chunk.content_hash,
                    "version": version,
                    "timestamp": segment.timestamp.isoformat(),
                }
            ],
            embeddings=[embedding],
        )

        logger.info(
            "Stored chunk v%d (hash=%s) from %s",
            version,
            chunk.content_hash[:12],
            chunk.url,
        )
        return segment

    def store_chunks(self, chunks: list[ScrapedChunk]) -> list[RulesSegment]:
        """Store multiple chunks, skipping duplicates (SC-003).

        Args:
            chunks: List of scraped chunks.

        Returns:
            List of stored ``RulesSegment`` objects.
        """
        segments: list[RulesSegment] = []
        for chunk in chunks:
            segment = self.store_chunk(chunk)
            segments.append(segment)
        return segments

    def search(
        self,
        query: str,
        n_results: int = 5,
    ) -> list[dict[str, Any]]:
        """Search for rules by semantic similarity.

        Args:
            query: Natural language search query.
            n_results: Maximum results to return.

        Returns:
            List of result dicts with document, metadata, and distance.
        """
        query_embedding = self._embedder.embed(query)
        raw_results = self._store.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
        )

        results: list[dict[str, Any]] = []
        documents = raw_results.get("documents", [[]])[0]
        metadatas = raw_results.get("metadatas", [[]])[0]
        distances = raw_results.get("distances", [[]])[0]

        for doc, meta, dist in zip(documents, metadatas, distances):
            results.append(
                {
                    "content": doc,
                    "metadata": meta,
                    "distance": dist,
                }
            )
        return results

    def _find_by_hash(self, content_hash: str) -> RulesSegment | None:
        """Look up an existing segment by content hash."""
        try:
            result = self._store.get(where={"content_hash": content_hash})
            docs: list[str] = result.get("documents", [])
            if docs:
                metas: list[dict[str, Any]] = result.get("metadatas", [])
                meta = metas[0] if metas else {}
                return RulesSegment(
                    url=meta.get("url", "https://unknown"),
                    content_markdown=docs[0],
                    content_hash=content_hash,
                    version=int(meta.get("version", 1)),
                )
        except Exception:
            pass
        return None

    def _get_next_version(self, url: str) -> int:
        """Get the next version number for a URL."""
        try:
            result = self._store.get(where={"url": url})
            metas: list[dict[str, Any]] = result.get("metadatas", [])
            if metas:
                versions = [int(m.get("version", 1)) for m in metas]
                return max(versions) + 1
        except Exception:
            pass
        return 1
