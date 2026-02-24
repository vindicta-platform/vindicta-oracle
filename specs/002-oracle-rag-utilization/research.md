# Research: Oracle RAG Utilization

**Feature**: `002-oracle-rag-utilization`  
**Created**: 2026-02-23  
**Purpose**: Resolve technical unknowns and document design decisions before implementation.

---

## R-001: MCP Client Library Selection

**Decision**: Use the official `mcp` Python SDK (`pip install mcp`).

**Rationale**: The foundation's RAG server is built on the MCP SDK (`mcp` package). Using the same SDK for the client ensures wire-level compatibility. The SDK provides both `stdio` and `SSE` transports, session management, and typed tool call/response interfaces.

**Alternatives considered**:
- **Raw HTTP/SSE client**: Lower dependency count but requires manual protocol handling (JSON-RPC framing, session lifecycle). Not worth the maintenance burden.
- **httpx-based wrapper**: Good for REST APIs but MCP uses JSON-RPC over transports, not REST. Would require reimplementing the protocol.

---

## R-002: Fallback Cache Backend

**Decision**: Use `diskcache` (Apache 2.0 license) for the write-through fallback cache.

**Rationale**: `diskcache` is a mature, pure-Python disk-backed key-value store built on SQLite. It supports atomic writes, size limits, and automatic eviction — all useful properties for a write-through cache. Zero-configuration compared to running a separate Redis/memcached.

**Alternatives considered**:
- **`shelve` (stdlib)**: Not thread-safe, no built-in size limits, poor performance under concurrent access.
- **`sqlite3` (stdlib)**: Zero-dependency but requires manual schema management. `diskcache` wraps SQLite with a cleaner API.
- **In-memory `dict`**: Loses cache on restart, defeating the purpose of fallback during outages.

---

## R-003: Import Namespace — `meta_oracle` vs `vindicta_oracle`

**Decision**: The existing oracle codebase uses `meta_oracle` as the import namespace (all imports are `from meta_oracle.xxx`). New RAG code will use the same namespace (`meta_oracle.rag.xxx`) for consistency until a full namespace migration is planned.

**Rationale**: Mixing `vindicta_oracle` and `meta_oracle` imports in the same codebase creates confusion. A namespace migration is out of scope for this feature.

**Impact on plan**: File paths in the plan reference `src/vindicta_oracle/rag/` (the disk layout), but Python imports will be `from meta_oracle.rag.xxx`. The `pyproject.toml` already maps `src/vindicta_oracle` → `meta_oracle` via `hatch` build config.

---

## R-004: VindictaModel Inheritance for Oracle Models

**Decision**: New RAG-specific domain models (`RAGQuery`, `RulesContextPackage`, etc.) will inherit from `VindictaModel` and be created within `vindicta-foundation/src/vindicta_foundation/models/` and exported via `__init__.py`.

**Rationale**: The Constitution §II strictly mandates that all domain models inherit from `VindictaModel` and are exported in the foundation package. While existing legacy oracle models use `pydantic.BaseModel`, Constitution rules are non-negotiable. Thus, new models must comply with Tier 1 and Tier 2 laws, residing in the foundation and inheriting `VindictaModel`.

**Impact on plan**: New models will be added to `vindicta-foundation` rather than `vindicta-oracle`.

---

## R-005: Context Window Budget Truncation Strategy

**Decision**: Relevance-ranked truncation using the `relevance_score` returned by ChromaDB's distance metric. Segments are sorted by relevance score (ascending distance = highest relevance), then included greedily until the character budget is exhausted.

**Rationale**: ChromaDB already returns distance/similarity scores with each result. Reusing these avoids a second-pass ranking step. The greedy approach is simple, deterministic, and easy to test.

**Alternatives considered**:
- **LLM-based re-ranking**: Expensive, introduces latency, requires an additional model call. Overkill for MVP.
- **Round-robin by unit**: Fair but ignores which units have more complex/important rules. Relevance-based is more useful.

---

## R-006: Batch Query MCP Interface

**Decision**: The oracle's `RAGClient.batch_query()` will accept a list of unit names and issue a single MCP tool call if the foundation's `search_40k_rules` tool supports `unit_names: list[str]`. If not (MVP), the client internally loops over individual calls and aggregates.

**Rationale**: Single-call batch is preferred for latency. However, the foundation's MCP server may initially only support single-query semantics. The oracle's batch interface should abstract this so callers don't care about the underlying transport mode.

**Foundation dependency**: The `search_40k_rules` tool in `005-rag-pipeline` currently accepts `query_text: str` and `agent_id: str`. A `unit_names` list parameter would need to be added upstream (or a separate `batch_search_40k_rules` tool). Until then, the oracle loops internally.
