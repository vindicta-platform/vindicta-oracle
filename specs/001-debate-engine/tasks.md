# Tasks: Debate Engine Foundation

**Feature**: Debate Engine Foundation
**Branch**: `001-debate-engine`
**Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

## Phase 1: Setup

- [ ] T001 Initialize package structure `src/meta_oracle/engine/`, `src/meta_oracle/agents/`, `src/meta_oracle/models/`, `src/meta_oracle/judging/` with `__init__.py`.
- [ ] T002 Update `pyproject.toml` with `vindicta-core` and `primordia-ai` dependencies as required.

## Phase 2: Foundational Data Models

- [ ] T003 Implement `DebateResult`, `DebateRound` and `Proposal` in `src/meta_oracle/models/debate_result.py` extending canonical standard models.
- [ ] T004 Implement Agent protocol `DebateAgent` exposing `propose()` and `argue()` in `src/meta_oracle/agents/protocol.py`.
- [ ] T005 [P] Create the transcript recorder models logic in `src/meta_oracle/models/transcript.py`.

## Phase 3: User Story 2 & 4 - Agent Interface and Stub Agents (P1)

- [ ] T006 [US2] Implement `AggressiveAgent` stub deriving from `DebateAgent`.
- [ ] T007 [US2] Implement `DefensiveAgent` stub deriving from `DebateAgent`.
- [ ] T008 [US2] Implement `BalancedAgent` stub deriving from `DebateAgent`.
- [ ] T009 [US2] Create unit tests in `tests/test_agents.py` validating scoring weights per agent type.

## Phase 4: User Story 1 - Debate Engine Orchestration (P1)

- [ ] T010 [US1] Implement `DebateEngine` core class in `src/meta_oracle/engine/debate_engine.py` handling round orchestration.
- [ ] T011 [US1] Build logic to instantiate engine with configured stub agents and trigger `propose()` and `argue()` in correct order.
- [ ] T012 [US1] Implement `scoring_judge.py` mapping to Judge functionality returning the winning proposal.
- [ ] T013 [US1] Build integration tests in `tests/test_debate_engine.py` simulating multi-round loops and asserting `< 500ms` bounds.

## Phase 5: User Story 3 - Audit Trail Generation (P2)

- [ ] T014 [US3] Ensure `DebateEngine` automatically records arguments per round and composes the final transcript.
- [ ] T015 [US3] Build serialization support JSON conversion for the transcript.
- [ ] T016 [US3] Enforce logging of timestamp entries via `Transcript`.

## Phase 6: Polish
- [ ] T017 Run `uv run pytest tests/ -v`.
- [ ] T018 Run `uv run mypy src/meta_oracle/ --strict`.
- [ ] T019 Run `ruff check .` and formatting.
