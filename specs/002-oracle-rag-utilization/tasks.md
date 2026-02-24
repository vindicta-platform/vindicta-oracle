# Tasks: Oracle RAG Utilization

**Input**: Design documents from `/specs/002-oracle-rag-utilization/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅

**Tests**: Included — spec defines 90% coverage mandate (Constitution V) and plan details test structure.

**Organization**: Tasks grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the `rag/` package, add dependencies, define shared models

- [ ] T001 Create `src/vindicta_oracle/rag/` package directory with `__init__.py` exporting `RAGClient`, `ContextAssembler`, `GradingDataAssembler`, `FallbackCache` in `src/vindicta_oracle/rag/__init__.py`
- [ ] T002 Add `mcp` and `diskcache` to project dependencies in `pyproject.toml`
- [ ] T003 [P] Create `QueryType` and `RetrievalMode` enums and all RAG domain models (`RAGQuery`, `RetrievedSegment`, `UnitStats`, `RulesContextPackage`, `GradingDataBundle`, `MetaSnapshot`, `FallbackCacheEntry`) in `vindicta-foundation/src/vindicta_foundation/models/rag_oracle.py`, ensuring they inherit from `VindictaModel` and are exported in `vindicta-foundation/src/vindicta_foundation/models/__init__.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core RAG client and fallback cache — MUST be complete before any user story

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement `RAGClient` class with `query()`, `batch_query()`, `connect()`, `disconnect()`, and context manager support using MCP SDK in `src/vindicta_oracle/rag/client.py`
- [ ] T005 [P] Implement `FallbackCache` class with `get()`, `put()`, `is_stale()` using `diskcache` in `src/vindicta_oracle/rag/fallback_cache.py`
- [ ] T006 [P] Write unit tests for `RAGClient` with mocked MCP SDK transport (query, batch_query, connection lifecycle, error handling) in `tests/unit/test_rag_client.py`
- [ ] T007 [P] Write unit tests for `FallbackCache` (put/get round-trip, cache miss returns None, staleness check, write-through on success) in `tests/unit/test_fallback_cache.py`

**Checkpoint**: RAGClient and FallbackCache are functional and independently tested

---

## Phase 3: User Story 1 — Grounded Debate with RAG-Backed Rules (Priority: P1) 🎯 MVP

**Goal**: Debate Engine fetches rules from the RAG server and injects them into agent context so Rule-Sage can verify `[RULE-{segment_id}]` citations.

**Independent Test**: Initiate a debate round for a known unit and verify the transcript contains citations whose `[RULE-{segment_id}]` tags match entries returned by the RAG server.

### Tests for User Story 1

- [ ] T008 [P] [US1] Write unit tests for `ContextAssembler` (batch assembly, version filtering, relevance truncation at 32K char budget, fallback to cache on client error, provenance tracking) in `tests/unit/test_context_assembler.py`

### Implementation for User Story 1

- [ ] T009 [US1] Implement `ContextAssembler` class with `assemble(unit_names, context_budget)` method — batch-fetches rules via `RAGClient`, filters to latest version per segment (FR-003 tiebreak by `segment_id`), applies relevance-ranked truncation (FR-008), falls back to `FallbackCache` on error, and records provenance (FR-009) in `src/vindicta_oracle/rag/context_assembler.py`
- [ ] T010 [US1] Add `rules_context: RulesContextPackage | None = None` field to `DebateContext` in `src/vindicta_oracle/models.py`
- [ ] T011 [US1] Add `rag_segments_used: list[str] = Field(default_factory=list)` field to `DebateTranscript` in `src/vindicta_oracle/models.py`
- [ ] T012 [US1] Modify `DebateEngine.__init__` to accept optional `context_assembler: ContextAssembler` parameter in `src/vindicta_oracle/engine.py`
- [ ] T013 [US1] Modify `DebateEngine.run_debate` to call `context_assembler.assemble()` before distributing context to agents, inject `RulesContextPackage` into `DebateContext.rules_context`, log retrieval mode (live/cached), and populate `DebateTranscript.rag_segments_used` in `src/vindicta_oracle/engine.py`

**Checkpoint**: Debate Engine with ContextAssembler produces transcripts with RAG-backed citations and audit trail

---

## Phase 4: User Story 2 — Dynamic List Grading Against the Current Meta (Priority: P1)

**Goal**: List Grader fetches unit stats and point costs from the RAG server to compute grades using live data.

**Independent Test**: Submit a list containing a unit whose point cost recently changed and verify the grade calculation uses the updated cost.

### Tests for User Story 2

- [ ] T014 [P] [US2] Write unit tests for `GradingDataAssembler` (unit data resolution from RAG, markdown-to-UnitStats regex parsing, partial bundle with warnings for unresolved units, provenance metadata) in `tests/unit/test_grading_data.py`

### Implementation for User Story 2

- [ ] T015 [US2] Implement `GradingDataAssembler` class with `fetch_unit_data(army_list)` method — queries RAG server for each unit, parses raw markdown into `UnitStats` using regex/heuristic extraction (FR-010), handles unresolved units with warnings (FR-007), and tracks provenance in `src/vindicta_oracle/rag/grading_data.py`
- [ ] T016 [US2] Modify `ListGrader.__init__` to accept optional `grading_data_assembler: GradingDataAssembler` parameter in `src/vindicta_oracle/grader.py`
- [ ] T017 [US2] Modify `ListGrader.grade` to call `grading_data_assembler.fetch_unit_data()` for live stats before scoring, pass `GradingDataBundle` warnings through to `GradeResponse.metadata` in `src/vindicta_oracle/grader.py`
- [ ] T018 [US2] Add `meta_context: dict | None = None` field to `GradeResponse` in `src/vindicta_oracle/models.py`

**Checkpoint**: List Grader with GradingDataAssembler grades lists using live RAG data with full provenance

---

## Phase 5: User Story 3 — Pre-Debate Context Assembly (Priority: P2)

**Goal**: Batch pre-fetch all rules for a candidate list before debate begins, reducing per-turn latency.

**Independent Test**: Measure RAG server call count and debate latency for a 3-round debate with and without pre-fetch, verify fewer total requests with pre-fetch.

### Tests for User Story 3

- [ ] T018a [P] [US3] Write unit tests for `ContextAssembler` batch pre-fetch entry point (unit name deduplication, fallback, context package creation) in `tests/unit/test_context_assembler_prefetch.py`

### Implementation for User Story 3

- [ ] T019 [US3] Add batch pre-fetch entry point to `ContextAssembler` — deduplicate unit names from the candidate list, issue a single `batch_query()`, and cache all results in `FallbackCache` in `src/vindicta_oracle/rag/context_assembler.py`
- [ ] T020 [US3] Modify `DebateEngine.run_debate` to invoke batch pre-fetch before the first round when `context_assembler` is present, skipping per-round individual queries in `src/vindicta_oracle/engine.py`

**Checkpoint**: Pre-fetch path issues fewer total RAG calls and agents share a consistent context base

---

## Phase 6: User Story 4 — Meta Snapshot for Comparative Grading (Priority: P3)

**Goal**: List Grader enriches grades with aggregate meta statistics (faction win rates, popular units).

**Independent Test**: Grade the same list with and without meta context enabled, verify the meta-aware grade includes contextual commentary.

### Tests for User Story 4

- [ ] T020a [P] [US4] Write unit tests for `GradingDataAssembler.fetch_meta_context` (fetching and structuring `MetaSnapshot` from RAG, returning `None` gracefully on miss) in `tests/unit/test_grading_data_meta.py`

### Implementation for User Story 4

- [ ] T021 [US4] Implement `GradingDataAssembler.fetch_meta_context(faction)` returning `MetaSnapshot | None` — queries RAG server for aggregate faction data in `src/vindicta_oracle/rag/grading_data.py`
- [ ] T022 [US4] Modify `ListGrader.grade` to optionally call `fetch_meta_context()` and populate `GradeResponse.meta_context` field in `src/vindicta_oracle/grader.py`

**Checkpoint**: List grades include meta context when available

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Integration testing, documentation, and final quality checks

- [ ] T023 [P] Write integration test with mock MCP server fixture — verify `DebateEngine` with `ContextAssembler` produces transcript with `rag_segments_used` populated, and `ListGrader` with `GradingDataAssembler` includes unit data provenance in `tests/integration/test_rag_integration.py`
- [ ] T024 [P] Update `src/vindicta_oracle/rag/__init__.py` exports to include all public classes
- [ ] T025 Run full lint and type check suite: `ruff check .`, `ruff format --check .`, `mypy src/vindicta_oracle --strict`
- [ ] T026 Run full test suite with coverage: `uv run pytest tests/ -v --cov=vindicta_oracle --cov-report=term-missing` — verify ≥90% coverage

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (T003 models must exist for T004/T005)
- **US1 (Phase 3)**: Depends on Phase 2 (needs RAGClient + FallbackCache)
- **US2 (Phase 4)**: Depends on Phase 2 (needs RAGClient + FallbackCache). Independent of US1.
- **US3 (Phase 5)**: Depends on Phase 3 (uses ContextAssembler from US1)
- **US4 (Phase 6)**: Depends on Phase 4 (extends GradingDataAssembler from US2)
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **US1 (P1)**: ← Phase 2 only. No dependency on other stories.
- **US2 (P1)**: ← Phase 2 only. No dependency on other stories. **Can run in parallel with US1.**
- **US3 (P2)**: ← US1 (extends ContextAssembler batch pre-fetch)
- **US4 (P3)**: ← US2 (extends GradingDataAssembler meta context)

### Within Each User Story

- Tests written and failing before implementation
- Models before services
- Services before integration points
- Core implementation before engine/grader modifications

### Parallel Opportunities

- T002 and T003 can run in parallel (Phase 1)
- T004 and T005 can run in parallel (Phase 2)
- T006 and T007 can run in parallel (Phase 2 tests)
- **US1 and US2 can run entirely in parallel** after Phase 2
- T023 and T024 can run in parallel (Phase 7)

---

## Parallel Example: User Story 1 + User Story 2

```bash
# After Phase 2 completes, launch US1 and US2 in parallel:

# US1 track:
Task: T008 — Unit tests for ContextAssembler
Task: T009 — Implement ContextAssembler
Task: T010-T013 — DebateEngine integration

# US2 track (parallel):
Task: T014 — Unit tests for GradingDataAssembler
Task: T015 — Implement GradingDataAssembler
Task: T016-T018 — ListGrader integration
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (RAGClient + FallbackCache)
3. Complete Phase 3: US1 — Grounded Debate (ContextAssembler + DebateEngine integration)
4. Complete Phase 4: US2 — Dynamic List Grading (GradingDataAssembler + ListGrader integration)
5. **STOP and VALIDATE**: Both US1 and US2 should work independently
6. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. US1 (Debate) + US2 (Grading) → Test independently → **MVP!**
3. US3 (Pre-fetch) → Performance optimisation layer
4. US4 (Meta context) → Enrichment layer
5. Each story adds value without breaking previous stories

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- All tests use mocked MCP transports — no real RAG server needed until `005-rag-pipeline` is implemented
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
