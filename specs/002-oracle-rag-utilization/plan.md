# Implementation Plan: Oracle RAG Utilization

**Branch**: `002-oracle-rag-utilization` | **Date**: 2026-02-23 | **Spec**: [spec.md](file:///c:/Users/bfoxt/vindicta-playground/vindicta-oracle/specs/002-oracle-rag-utilization/spec.md)
**Input**: Feature specification from `specs/002-oracle-rag-utilization/spec.md`
**Upstream Dependency**: [005-rag-pipeline](file:///c:/Users/bfoxt/vindicta-playground/vindicta-foundation/specs/005-rag-pipeline/spec.md) (vindicta-foundation)

## Summary

This feature builds the **oracle-specific consumer layer** on top of the foundation's RAG pipeline (`005-rag-pipeline`). The foundation owns the full RAG infrastructure — scraper, ChromaDB storage, Ollama embeddings, and MCP server. This plan deliberately **does not** duplicate any of that. Instead, it implements:

1. An **MCP Client** (`RAGClient`) that connects to the foundation's MCP server to issue structured queries.
2. A **Fallback Cache** that snapshots the most recent successful retrieval per unit/topic, enabling degraded-mode operation when the RAG server is unreachable.
3. A **Context Assembler** that batch-fetches rules for all units in a candidate list and produces a `RulesContextPackage` for the Debate Engine.
4. A **Grading Data Bundle** assembler that fetches unit stats and point costs, producing a `GradingDataBundle` for the List Grader.
5. Integration hooks into the existing `DebateEngine` and `ListGrader` to consume RAG data.

> [!IMPORTANT]
> This feature depends on `vindicta-foundation/005-rag-pipeline` being implemented first. The MCP server must expose a `search_40k_rules` tool. The oracle only implements the **client** side.

## Technical Context

- **Language/Version**: Python 3.12+ (uv workspace)
- **Primary Dependencies**: `mcp` (MCP SDK client), `pydantic>=2.0`, `diskcache` (lightweight local fallback)
- **Upstream**: `vindicta-foundation` exposes `search_40k_rules` via MCP server; models `RulesSegment`, `AgentQuery` live in foundation.
- **Testing**: pytest (90% coverage mandate), `ruff`, `mypy`
- **Performance Goal**: Pre-debate context assembly < 3 seconds for 10-15 units (SC-003)

## Constitution Check

- [x] **Model Integrity**: New oracle models (`RAGQuery`, `RulesContextPackage`, `GradingDataBundle`, `FallbackCacheEntry`) will inherit from `VindictaModel`. To comply with Constitution §II, they will be defined in `vindicta-foundation` and exported via its `__init__.py`. See [R-004](file:///c:/Users/bfoxt/vindicta-playground/vindicta-oracle/specs/002-oracle-rag-utilization/research.md). (Constitution II)
- [x] **Quality Mandate**: `pytest` 90% coverage, `mypy` strict, `ruff` linting. (Constitution V)
- [x] **Environment**: `pyproject.toml` uses `pythonpath = ["src"]`. (Constitution Constraints)
- [ℹ] **Import Namespace**: Existing oracle code uses `meta_oracle` as the Python import namespace, not `vindicta_oracle`. New RAG code follows this convention (`meta_oracle.rag.xxx`). See [R-003](file:///c:/Users/bfoxt/vindicta-playground/vindicta-oracle/specs/002-oracle-rag-utilization/research.md).

## Proposed Changes

### RAG Client Layer

Thin MCP client wrapper responsible for all communication with the foundation's RAG server.

#### [NEW] [rag_client.py](file:///c:/Users/bfoxt/vindicta-playground/vindicta-oracle/src/vindicta_oracle/rag/client.py)

- `RAGClient` class wrapping the MCP SDK client
- `query(query: RAGQuery) -> list[RetrievedSegment]` — issues a single query to the MCP `search_40k_rules` tool
- `batch_query(queries: list[RAGQuery]) -> dict[str, list[RetrievedSegment]]` — issues multiple queries, returns results keyed by unit/topic
- Connection lifecycle management (`connect()`, `disconnect()`, context manager)
- Structured logging for all MCP interactions (NFR-001 from foundation spec)

---

### Fallback Cache

Local disk-based cache of the most recent successful RAG retrieval per unit/topic. Enables FR-005.

#### [NEW] [fallback_cache.py](file:///c:/Users/bfoxt/vindicta-playground/vindicta-oracle/src/vindicta_oracle/rag/fallback_cache.py)

- `FallbackCache` class using `diskcache` (or `shelve`/`sqlite3` if zero-dep preferred)
- `get(key: str) -> list[RetrievedSegment] | None` — retrieve cached segments
- `put(key: str, segments: list[RetrievedSegment]) -> None` — store/overwrite cached segments
- Auto-populated on every successful RAG query (write-through pattern)
- `is_stale(key: str, max_age: timedelta) -> bool` — staleness check for logging

---

### Context Assembler (Debate Engine)

Builds the `RulesContextPackage` for a debate session. Implements FR-001, FR-004, FR-006, FR-008.

#### [NEW] [context_assembler.py](file:///c:/Users/bfoxt/vindicta-playground/vindicta-oracle/src/vindicta_oracle/rag/context_assembler.py)

- `ContextAssembler` class, injected with `RAGClient` + `FallbackCache`
- `assemble(unit_names: list[str], context_budget: int) -> RulesContextPackage` — batch-fetches rules for all units, applies relevance-ranked truncation (FR-008), returns a sealed context package
- Version filtering: selects only the most recent version per segment (FR-003 from spec)
- Provenance tracking: records which segment IDs were included (FR-009)

---

### Grading Data Assembler (List Grader)

Builds the `GradingDataBundle` for list evaluation. Implements FR-002, FR-007.

#### [NEW] [grading_data.py](file:///c:/Users/bfoxt/vindicta-playground/vindicta-oracle/src/vindicta_oracle/rag/grading_data.py)

- `GradingDataAssembler` class, injected with `RAGClient` + `FallbackCache`
- `fetch_unit_data(army_list: ArmyList) -> GradingDataBundle` — retrieves current stats and point costs for every unit
- Handles unresolved units by returning a partial bundle with warnings (FR-007)
- Optional `fetch_meta_context(faction: str) -> MetaSnapshot | None` — retrieves aggregate faction meta data (P3, FR not numbered)

---

### Oracle Models

Oracle-specific Pydantic models that compose around the foundation's `RulesSegment`.

#### [NEW] [vindicta-foundation/src/vindicta_foundation/models/rag_oracle.py](file:///c:/Users/bfoxt/vindicta-playground/vindicta-foundation/src/vindicta_foundation/models/rag_oracle.py)

New models (all inherit `VindictaModel`):

| Model | Purpose | Key Fields |
|---|---|---|
| `RAGQuery` | Structured search request | `unit_names`, `query_type` (enum: unit_stats, weapon_profile, errata, meta_context), `version_filter` |
| `RetrievedSegment` | Single result from RAG server | `segment_id`, `content_markdown`, `relevance_score`, `version`, `retrieval_timestamp` |
| `RulesContextPackage` | Debate-round context bundle | `segments: list[RetrievedSegment]`, `unit_coverage: dict`, `budget_used: int`, `retrieval_mode` (live/cached) |
| `GradingDataBundle` | List-grading data bundle | `unit_data: dict[str, UnitStats]`, `unresolved_units: list[str]`, `provenance: dict`, `retrieval_mode` |
| `UnitStats` | Parsed unit statistics | `name`, `points_cost`, `toughness`, `wounds`, `save`, `weapons: list`, `abilities: list` |
| `MetaSnapshot` | Aggregate meta data | `faction`, `win_rate`, `popular_units`, `meta_commentary` |
| `FallbackCacheEntry` | Cache row wrapper | `key`, `segments`, `cached_at`, `source_query` |

---

### Integration Points

Minimal modifications to existing code to inject RAG data.

#### [MODIFY] [engine.py](file:///c:/Users/bfoxt/vindicta-playground/vindicta-oracle/src/vindicta_oracle/engine.py)

- Add optional `context_assembler: ContextAssembler` parameter to `__init__`
- In `run_debate()`: if assembler is provided, call `assemble()` before distributing context to agents
- Inject retrieved rules into `DebateContext.additional_context` (or a new field)
- Log retrieval mode (live/cached) on the transcript

#### [MODIFY] [grader.py](file:///c:/Users/bfoxt/vindicta-playground/vindicta-oracle/src/vindicta_oracle/grader.py)

- Add optional `grading_data_assembler: GradingDataAssembler` parameter to `__init__`
- In `grade()`: if assembler is provided, call `fetch_unit_data()` to retrieve live stats before grading
- Pass `GradingDataBundle` warnings through to `GradeResponse.metadata`
- Optionally call `fetch_meta_context()` and append `meta_context` section to response

#### [MODIFY] [models.py](file:///c:/Users/bfoxt/vindicta-playground/vindicta-oracle/src/vindicta_oracle/models.py)

- Add `rules_context: RulesContextPackage | None = None` field to `DebateContext`
- Add `rag_segments_used: list[str] = []` field to `DebateTranscript` for auditability (FR-009)
- Add `meta_context: dict | None = None` field to `GradeResponse`

---

### Package Init & Dependencies

#### [NEW] [__init__.py](file:///c:/Users/bfoxt/vindicta-playground/vindicta-oracle/src/vindicta_oracle/rag/__init__.py)

- Export `RAGClient`, `ContextAssembler`, `GradingDataAssembler`, `FallbackCache`

#### [MODIFY] [pyproject.toml](file:///c:/Users/bfoxt/vindicta-playground/vindicta-oracle/pyproject.toml)

- Add `mcp` to dependencies (MCP SDK client)
- Add `vindicta-foundation` as a workspace dependency

## Project Structure

```text
vindicta-oracle/src/vindicta_oracle/
├── rag/                           # NEW — all RAG consumer code
│   ├── __init__.py                # Package exports
│   ├── models.py                  # RAGQuery, RulesContextPackage, GradingDataBundle, etc.
│   ├── client.py                  # RAGClient (MCP SDK wrapper)
│   ├── fallback_cache.py          # FallbackCache (disk-backed)
│   ├── context_assembler.py       # ContextAssembler (debate pre-fetch)
│   └── grading_data.py            # GradingDataAssembler (list grader)
├── engine.py                      # MODIFIED — optional RAG injection
├── grader.py                      # MODIFIED — optional RAG injection
└── models.py                      # MODIFIED — new fields for RAG context

vindicta-oracle/tests/
├── unit/
│   ├── test_rag_client.py         # NEW
│   ├── test_fallback_cache.py     # NEW
│   ├── test_context_assembler.py  # NEW
│   └── test_grading_data.py       # NEW
└── integration/
    └── test_rag_integration.py    # NEW — end-to-end with mocked MCP server
```

## Verification Plan

### Automated Tests

All tests run via: `cd vindicta-oracle && uv run pytest tests/ -v --cov=vindicta_oracle --cov-report=term-missing`

1. **`tests/unit/test_rag_client.py`** — Mock the MCP SDK transport; verify `query()` sends correct tool name and args, `batch_query()` deduplicates, connection lifecycle works.
2. **`tests/unit/test_fallback_cache.py`** — Verify `put()`/`get()` round-trip, staleness check, cache miss returns `None`.
3. **`tests/unit/test_context_assembler.py`** — Mock `RAGClient`; verify batch assembly, version filtering (only latest), relevance truncation when exceeding budget, fallback to cache on client error.
4. **`tests/unit/test_grading_data.py`** — Mock `RAGClient`; verify unit data resolution, partial bundle with warnings for unresolved units, meta context fetch.
5. **`tests/integration/test_rag_integration.py`** — Spin up a mock MCP server fixture; verify `DebateEngine` with `ContextAssembler` produces a transcript with `rag_segments_used` populated; verify `ListGrader` with `GradingDataAssembler` includes unit data provenance.

### Lint & Type Checks

```bash
cd vindicta-oracle
uv run ruff check .
uv run ruff format --check .
uv run mypy src/vindicta_oracle --strict
```

### Manual Verification

> [!NOTE]
> Full end-to-end testing against the real foundation MCP server is deferred until `005-rag-pipeline` is implemented. All automated tests use mocked transports.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

*No violations detected. All models inherit `VindictaModel`. Strict adherence to Foundation axioms.*
