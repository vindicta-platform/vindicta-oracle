# Specification: List Grader API

**Feature**: List Grader API  
**Repository**: vindicta-platform/Meta-Oracle  
**Issue Reference**: #8  
**Version**: 1.3  
**Status**: ✅ Clarified  
**Last Updated**: 2026-02-06

---

## Executive Summary

The List Grader API exposes Meta-Oracle's AI council debate capability as a REST endpoint, allowing users to submit competitive army lists and receive structured grades, tactical analysis, and council verdicts.

---

## User Stories

### US-1: Competitive Player List Evaluation
**As a** competitive player,  
**I want to** submit my army list for AI evaluation,  
**So that** I can understand its strengths and weaknesses before a tournament.

### US-2: List Comparison Analysis
**As a** player preparing for a matchup,  
**I want to** receive a grade and analysis for my list,  
**So that** I can make informed decisions about unit choices and tactics.

### US-3: API Integration
**As a** Vindicta Portal developer,  
**I want to** call the List Grader API programmatically,  
**So that** I can integrate grading into the web UI.

---

## Acceptance Criteria

### AC-1: API Endpoint
- [ ] `POST /grade` endpoint accepts an army list payload
- [ ] Endpoint returns JSON response within 30 seconds
- [ ] Endpoint validates input schema and returns 400 for invalid requests

### AC-2: Grading Response
- [ ] Response includes a letter grade (A-F) with numeric score (0-100)
- [ ] Response includes structured analysis from each council agent
- [ ] Response includes final council verdict with confidence percentage

### AC-3: Council Integration
- [ ] Grading triggers a full 5-agent council debate
- [ ] Debate uses Home agent advocacy and Adversary critique
- [ ] Arbiter produces the final verdict

### AC-4: Error Handling
- [ ] Invalid list format returns 400 with descriptive error
- [ ] Quota exhaustion returns 429 with retry-after header
- [ ] Internal errors return 500 with correlation ID

---

## API Contract

### `POST /api/v1/grade`

#### Request Schema
```json
{
  "army_list": {
    "faction": "string",
    "points_limit": 2000,
    "units": [
      {
        "name": "string",
        "points": 150,
        "wargear": ["string"]
      }
    ],
    "detachment": "string"
  },
  "context": {
    "mission": "string (optional)",
    "opponent_faction": "string (optional)"
  }
}
```

#### Response Schema
```json
{
  "grade": "B+",
  "score": 78,
  "analysis": {
    "home_advocacy": "string",
    "adversary_critique": "string",
    "rule_sage_notes": "string",
    "arbiter_verdict": "string"
  },
  "council_verdict": {
    "prediction": "COMPETITIVE",
    "confidence": 0.72,
    "consensus_agents": ["Home", "Rule-Sage", "Arbiter"]
  },
  "metadata": {
    "debate_id": "uuid",
    "rounds": 3,
    "processing_time_ms": 2500
  }
}
```

---

## Integration Points

| Dependency | Role | Integration |
|------------|------|-------------|
| `DebateEngine` | Orchestration | Async debate session |
| `Agent-Auditor-SDK` | Quota | Pre-flight budget check |
| `WARScribe-Core` | Validation | List schema validation |
| `Primordia-AI` | Scoring | Tactical evaluation input |

---

## Clarification Cycle 1: Ambiguity Resolution

### Grading Scale Definition
| Grade | Score Range | Description |
|-------|-------------|-------------|
| A | 90-100 | Tournament-winning tier |
| B | 75-89 | Competitively viable |
| C | 60-74 | Average performance expected |
| D | 40-59 | Below average, exploitable weaknesses |
| F | 0-39 | Non-competitive |

### Decisions Made
1. **Grading formula**: Score = 0.6 × Council Consensus + 0.4 × Primordia Tactical Score
2. **Caching strategy**: No caching - always fresh debate
3. **Partial results**: Return 503 with partial transcript if debate cannot complete
4. **Authentication**: JWT required; anonymous requests return 401

---

## Clarification Cycle 2: Component Impact

### Files Requiring Modification

| File | Change Type | Impact |
|------|-------------|--------|
| `src/meta_oracle/api.py` | **[NEW]** | FastAPI router for `/grade` endpoint |
| `src/meta_oracle/grader.py` | **[NEW]** | Grading orchestration logic |
| `src/meta_oracle/models.py` | **[MODIFY]** | Add `GradeRequest`, `GradeResponse` Pydantic models |
| `src/meta_oracle/engine.py` | **[MODIFY]** | Expose `run_grading_session()` method |
| `pyproject.toml` | **[MODIFY]** | Add FastAPI, uvicorn dependencies |

---

## Clarification Cycle 3: Edge Case & Failure Analysis

### Failure Modes

| Scenario | Detection | Response |
|----------|-----------|----------|
| Invalid list JSON | Pydantic validation | 400 + validation errors |
| Empty units array | Schema check | 400 + "List must have at least 1 unit" |
| Quota exhausted | Agent-Auditor pre-check | 429 + retry-after header |
| Agent timeout | asyncio.wait_for | 504 + partial transcript |
| Ollama unavailable | Connection error | 503 + "AI service unavailable" |

### Edge Cases

| Case | Expected Behavior |
|------|-------------------|
| Single-unit list | Valid grading; may score F due to lack of synergy |
| 3000+ point list | Accept but warn; debates may run longer |
| Duplicate units | Valid; analyze point concentration risks |
| Missing wargear | Default to base loadout for analysis |
