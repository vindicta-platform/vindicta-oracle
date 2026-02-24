# Speckit Analysis Report: Oracle RAG Utilization

**Feature Branch**: `002-oracle-rag-utilization`
**Date**: 2026-02-23
**Artifacts Analyzed**: `spec.md`, `plan.md`, `data-model.md`, `tasks.md`

## Overall Assessment

| Criterion | Status | Notes |
|---|---|---|
| Spec → Plan alignment | ✅ Pass | All 9 FRs mapped to plan components |
| Plan → Tasks alignment | ✅ Pass | Every plan component has a corresponding task phase |
| Data Model completeness | ✅ Pass | All spec Key Entities have model definitions |
| FR coverage | ✅ Pass | All FRs traceable to tasks |
| SC coverage | ⚠️ Partial | SC-001 depends on agent behavior outside this feature |
| Edge case resolution | ✅ Pass | All 5 edge cases addressed in clarifications or plan |
| Constitution compliance | ✅ Pass | All models inherit VindictaModel; quality mandates met |

## FR Traceability Matrix

| FR | Spec Description | Plan Component | Task Phase | Covered? |
|---|---|---|---|---|
| FR-001 | Debate Engine queries RAG for weapons/abilities/errata | Context Assembler | Phase 4 | ✅ |
| FR-002 | List Grader queries RAG for stats/points | Grading Data Assembler | Phase 5 | ✅ |
| FR-003 | Use only most recent version when multiple returned | Context Assembler + Grading Data | Phase 4, 5 | ✅ |
| FR-004 | Batch query mode for multiple units | RAG Client `batch_query()` | Phase 2 | ✅ |
| FR-005 | Fallback to cached snapshot when server unreachable | Fallback Cache | Phase 3, 4, 5 | ✅ |
| FR-006 | Inject segments into agent context for Rule-Sage audit | Context Assembler + Engine integration | Phase 4, 6 | ✅ |
| FR-007 | Partial grade with warnings for unresolved units | Grading Data Assembler | Phase 5, 6 | ✅ |
| FR-008 | Relevance-ranked truncation within budget | Context Assembler | Phase 4 | ✅ |
| FR-009 | Record which segments used for auditability | Models + Integration hooks | Phase 1, 6 | ✅ |

## SC Traceability Matrix

| SC | Description | Verification | Notes |
|---|---|---|---|
| SC-001 | Zero ungrounded citations | Integration test verifies `rag_segments_used` populated | ⚠️ Full verification requires agent citation behavior (outside this feature scope) |
| SC-002 | Grades reflect changes within one ingest cycle | Grading Data Assembler uses live RAG data | ✅ Achievable if foundation ingest runs on schedule |
| SC-003 | Pre-debate assembly < 3 seconds | Integration test can benchmark | ✅ Measurable in test |
| SC-004 | 100% fallback success rate | Fallback cache tests | ✅ Tested in Phase 3, 4, 5 |
| SC-005 | 95% unit lookup resolution | Depends on foundation data completeness | ⚠️ Not oracle's responsibility, but oracle reports `unresolved_units` |

## Critical Findings

### Finding 1: SC-001 Requires Agent Protocol Changes (Severity: Low)

SC-001 ("zero ungrounded citations") depends on agents actually using `[RULE-{segment_id}]` format and Rule-Sage actively auditing. The oracle RAG utilization feature provides the data and provenance infrastructure, but the citation enforcement is an agent-level concern that should be tracked in `001-debate-engine` or a future agent protocol update.

**Recommendation**: Add a tracking note in `001-debate-engine` spec for citation format enforcement. No changes needed in this feature.

---

### Finding 2: `meta_oracle` vs `vindicta_oracle` Import Inconsistency (Severity: Medium)

The existing codebase (`engine.py`, `grader.py`, `models.py`, `protocol.py`) uses `from meta_oracle.models import ...` imports, but the package is located at `src/vindicta_oracle/`. This suggests a package rename happened without updating all imports, or a module alias exists.

**Recommendation**: Verify the `pyproject.toml` package mapping. New RAG code should import from `vindicta_oracle.rag.models`. The import inconsistency is pre-existing and should be addressed in a separate cleanup task, not in this feature.

---

### Finding 3: `diskcache` Dependency Decision (Severity: Low)

The plan proposes `diskcache` for the fallback cache but notes `shelve` or `sqlite3` as zero-dep alternatives. The data-model defines `FallbackCacheEntry` with serializable fields, so any backend works.

**Recommendation**: Use `sqlite3` (stdlib) for the MVP to avoid adding a new dependency. Only switch to `diskcache` if serialization complexity justifies it.

---

### Finding 4: `VindictaModel` Import Path (Severity: Low)

The plan and data-model state all models inherit from `VindictaModel` via `vindicta_foundation.models.base`. Verify this import is available in the oracle's dependency graph (the workspace `pyproject.toml` must list `vindicta-foundation` as a dependency).

**Recommendation**: Confirm during Phase 1 model implementation. Already noted in `pyproject.toml` modification tasks in Phase 6.

## Edge Case Resolution Summary

| Edge Case | Resolution |
|---|---|
| RAG returns stale data (ingest lag) | Oracle uses whatever the RAG server returns; staleness is a foundation/ingest concern. Fallback cache `is_stale()` logs warnings. |
| Zero results for misspelled unit query | `GradingDataAssembler` adds to `unresolved_units` list; `ContextAssembler` sets `unit_coverage[name] = False`. |
| Batch pre-fetch exceeds response size (20+ units) | `ContextAssembler` applies `context_budget` truncation after retrieval (FR-008). |
| Mid-debate RAG outage after pre-fetch | Pre-fetched `RulesContextPackage` is already sealed and distributed. No mid-debate queries needed (P2 optimization). |
| Identical timestamps on same datasheet | Tiebreak by `segment_id` lexicographic order (see clarification Q5). |

## Conclusion

The `002-oracle-rag-utilization` spec, plan, data-model, and tasks are **well-aligned**. All functional requirements map cleanly to implementation tasks. The primary risk is the unimplemented upstream dependency (`005-rag-pipeline`), which is correctly identified and mitigated by mocked transports in all tests. Two minor pre-existing issues (import naming inconsistency, VindictaModel import path) should be validated during implementation but do not block planning approval.
