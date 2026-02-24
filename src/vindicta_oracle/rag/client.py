"""MCP Client wrapper for the RAG server."""

import json
import logging
from contextlib import AsyncExitStack, asynccontextmanager
from typing import Dict, List

from mcp import ClientSession
from mcp.client.sse import sse_client

from meta_oracle.rag.models import RAGQuery, RetrievedSegment

logger = logging.getLogger(__name__)


class RAGServerUnreachableError(Exception):
    """Raised when the RAG server cannot be reached."""
    pass


class RAGClient:
    """Thin wrapper around the MCP SDK for rules lookups."""

    def __init__(self, server_url: str):
        self.server_url = server_url
        self._session: ClientSession | None = None
        self._exit_stack: AsyncExitStack | None = None

    async def connect(self) -> None:
        """Connect to the MCP server via SSE."""
        if self._session:
            return

        try:
            self._exit_stack = AsyncExitStack()

            # Use SSE transport for HTTP servers
            read_stream, write_stream = await self._exit_stack.enter_async_context(
                sse_client(self.server_url)
            )

            self._session = await self._exit_stack.enter_async_context(
                ClientSession(read_stream, write_stream)
            )

            await self._session.initialize()
            logger.info("Connected to RAG server at %s", self.server_url)

        except Exception as e:
            logger.error("Failed to connect to RAG server %s: %s", self.server_url, str(e))
            await self.disconnect()
            raise RAGServerUnreachableError(f"Cannot reach {self.server_url}") from e

    async def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        if self._exit_stack:
            await self._exit_stack.aclose()
        self._session = None
        self._exit_stack = None
        logger.debug("Disconnected from RAG server")

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()

    async def query(self, request: RAGQuery) -> List[RetrievedSegment]:
        """Query the RAG server for a single set of parameters."""
        if not self._session:
            raise RAGServerUnreachableError("Not connected to RAG server")

        try:
            logger.info("Executing RAG query for units: %s", request.unit_names)
            response = await self._session.call_tool(
                "search_40k_rules",
                arguments={
                    "unit_names": request.unit_names,
                    "query_type": request.query_type.value,
                    "version_filter": request.version_filter,
                    "agent_id": request.agent_id
                }
            )

            segments = []

            if response.content:
                for item in response.content:
                    if hasattr(item, "text"):
                        try:
                            payload = json.loads(item.text)
                            # Assume tool returns a dict with "segments"
                            for seg in payload.get("segments", []):
                                segments.append(RetrievedSegment.model_validate(seg))
                        except json.JSONDecodeError:
                            logger.error("Failed to decode RAG server JSON response from MCP tool")
                        except Exception as inner_e:
                            logger.error("Error validating returned RAG segments: %s", inner_e)

            return segments

        except Exception as e:
            logger.error("RAG query failed: %s", str(e))
            raise RAGServerUnreachableError("Communication with RAG server failed") from e

    async def batch_query(self, queries: List[RAGQuery]) -> Dict[str, List[RetrievedSegment]]:
        """Execute multiple RAG queries. Deduplicates overlapping unit names."""
        if not queries:
            return {}

        # Group by query type to aggregate efficiently
        by_type = {}
        for q in queries:
            by_type.setdefault(q.query_type, []).append(q)

        results: Dict[str, List[RetrievedSegment]] = {}

        for q_type, type_queries in by_type.items():
            all_units = set()
            for q in type_queries:
                for unit in q.unit_names:
                    all_units.add(unit)

            if all_units:
                # Single MCP call handling multiple unit names for the same query type
                batch_req = RAGQuery(
                    unit_names=list(all_units),
                    query_type=q_type,
                    version_filter=next(
                        (q.version_filter for q in type_queries if q.version_filter is not None),
                        None
                    ),
                    agent_id="oracle_batch"
                )

                try:
                    segments = await self.query(batch_req)
                    
                    for unit in all_units:
                        # In reality, segments would map to specific units.
                        # For now we bundle everything together to return to caller.
                        results[unit] = segments
                except RAGServerUnreachableError:
                    raise

        return results
