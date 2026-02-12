# Implementation Plan: List Grader API

## Proposed Changes

### API Layer

#### [NEW] `src/meta_oracle/api.py`
- Create FastAPI `APIRouter` with prefix `/api/v1`
- Implement `POST /grade` endpoint accepting `GradeRequest`
- Return `GradeResponse` with council verdict
- Include error handlers for 400/429/503/504

#### [NEW] `src/meta_oracle/grader.py`
- `ListGrader` class with async `grade()` method
- Integrate quota pre-check via Agent-Auditor-SDK (stub)
- Calculate final score: `0.6 * council_consensus + 0.4 * primordia_score`
- Map numeric score to letter grade (A-F)

### Core Engine

#### [MODIFY] `src/meta_oracle/models.py`
Add Pydantic models: `Unit`, `ArmyList`, `GradeRequest`, `GradeResponse`

#### [MODIFY] `src/meta_oracle/engine.py`
Add `run_grading_session(army_list: ArmyList) -> DebateResult`

#### [MODIFY] `pyproject.toml`
Add FastAPI, uvicorn dependencies under `[project.optional-dependencies].api`

---

## Verification Plan

### Automated Tests
- `tests/test_grader.py`: Unit tests for grading logic
- `tests/test_api.py`: Integration tests for API endpoint

### Run Command
```bash
uv run pytest tests/test_grader.py tests/test_api.py -v
```

### Manual Integration Test
```bash
uv run uvicorn meta_oracle.api:app --port 8000
curl -X POST http://localhost:8000/api/v1/grade \
  -H "Content-Type: application/json" \
  -d '{"army_list": {"faction": "Space Marines", "units": [{"name": "Captain", "points": 100}]}}'
```

---

*Last Updated: 2026-02-06*
