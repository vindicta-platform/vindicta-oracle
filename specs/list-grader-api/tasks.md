# Tasks: List Grader API

## Phase 1: Foundation

### T-001: Add GradeRequest/GradeResponse Models
**File**: `src/meta_oracle/models.py`  
**Issue**: [#17](https://github.com/vindicta-platform/Meta-Oracle/issues/17)

### T-002: Add FastAPI Dependencies
**File**: `pyproject.toml`  
**Issue**: [#18](https://github.com/vindicta-platform/Meta-Oracle/issues/18)

---

## Phase 2: API Implementation

### T-003: Implement ListGrader Class
**File**: `src/meta_oracle/grader.py` [NEW]  
**Issue**: [#19](https://github.com/vindicta-platform/Meta-Oracle/issues/19)

### T-004: Expose Engine Grading Interface
**File**: `src/meta_oracle/engine.py`  
**Issue**: [#20](https://github.com/vindicta-platform/Meta-Oracle/issues/20)

### T-005: Create FastAPI Router
**File**: `src/meta_oracle/api.py` [NEW]  
**Issue**: [#21](https://github.com/vindicta-platform/Meta-Oracle/issues/21)

---

## Phase 3: Testing

### T-006: Unit Tests for Grader
**File**: `tests/test_grader.py` [NEW]  
**Issue**: [#22](https://github.com/vindicta-platform/Meta-Oracle/issues/22)

### T-007: API Integration Tests
**File**: `tests/test_api.py` [NEW]  
**Issue**: [#23](https://github.com/vindicta-platform/Meta-Oracle/issues/23)

### T-008: Documentation Update
**File**: `README.md`  
**Issue**: [#24](https://github.com/vindicta-platform/Meta-Oracle/issues/24)

---

## Summary

| Phase | Tasks | Effort | Issues |
|-------|-------|--------|--------|
| Foundation | T-001, T-002 | 1.25 hrs | #17, #18 |
| API Implementation | T-003, T-004, T-005 | 4.5 hrs | #19, #20, #21 |
| Testing | T-006, T-007, T-008 | 2.5 hrs | #22, #23, #24 |
| **Total** | 8 tasks | ~8.25 hrs | 8 issues |
