# Feature Proposal: Meta-Oracle Match Prediction API

**Proposal ID**: FEAT-011  
**Author**: Unified Product Architect (Autonomous)  
**Created**: 2026-02-01  
**Status**: Draft  
**Priority**: High  
**Target Repository**: Meta-Oracle  

---

## Part A: Software Design Document (SDD)

### 1. Executive Summary

Expose a public API for match predictions, allowing players to query expected win probabilities, optimal secondaries, and key matchup insights based on faction/subfaction combinations.

### 2. System Architecture

#### 2.1 Current State
- Internal analytics engine
- No public API
- Batch-processed statistics

#### 2.2 Proposed Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                 Meta-Oracle Prediction API                      │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                   API Gateway                           │    │
│  │   /predict/match  |  /stats/faction  |  /recommend      │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                  │
│                              ▼                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              Prediction Engine                          │    │
│  │   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │    │
│  │   │ Win Rate    │  │ Secondary   │  │  Matchup    │     │    │
│  │   │ Predictor   │  │ Recommender │  │  Analyzer   │     │    │
│  │   └─────────────┘  └─────────────┘  └─────────────┘     │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                  │
│                              ▼                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              Historical Data Store                      │    │
│  │   Battle logs | Tournament results | Meta snapshots     │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

#### 2.3 File Changes

```
Meta-Oracle/
├── src/
│   └── meta_oracle/
│       ├── api/
│       │   ├── __init__.py      [NEW]
│       │   ├── routes.py        [NEW] FastAPI routes
│       │   └── schemas.py       [NEW] Request/response models
│       ├── prediction/
│       │   ├── match.py         [NEW] Match outcome predictor
│       │   ├── secondaries.py   [NEW] Secondary optimizer
│       │   └── matchups.py      [NEW] Matchup analysis
│       └── data/
│           └── aggregator.py    [MODIFY] API-friendly queries
├── tests/
│   └── test_prediction_api.py   [NEW]
└── docs/
    └── api.md                   [NEW] API documentation
```

### 3. API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/predict/match` | Predict match outcome |
| GET | `/api/v1/stats/faction/{id}` | Faction win rates |
| GET | `/api/v1/stats/matchup` | Head-to-head stats |
| POST | `/api/v1/recommend/secondaries` | Optimal secondary objectives |
| GET | `/api/v1/meta/trends` | Current meta trends |

### 4. Prediction Request/Response

```python
class MatchPredictionRequest(BaseModel):
    player1_faction: str
    player1_subfaction: Optional[str]
    player2_faction: str
    player2_subfaction: Optional[str]
    mission: Optional[str]
    points_limit: int = 2000

class MatchPredictionResponse(BaseModel):
    player1_win_probability: float  # 0.0 - 1.0
    player2_win_probability: float
    confidence: float               # Algorithm confidence
    key_factors: list[str]          # "Player 1 has strong anti-vehicle"
    recommended_secondaries: dict[str, list[str]]
    sample_size: int                # Games analyzed
```

### 5. Rate Limiting

| Tier | Requests/Hour | Cache TTL |
|------|---------------|-----------|
| Anonymous | 10 | 1 hour |
| Free Member | 50 | 30 min |
| Supporter | 200 | 15 min |
| Champion | 1000 | 5 min |

### 6. Data Sources

- Historical battle logs from Vindicta platform
- Tournament results (40kstats integration potential)
- ELO-weighted outcomes
- Regularly updated meta snapshots

---

## Part B: Behavior Driven Development (BDD)

### User Stories

#### US-001: Pre-Game Analysis
**As a** tournament player  
**I want to** check my matchup before a game  
**So that** I can prepare an optimal strategy

#### US-002: Secondary Selection
**As a** competitive player  
**I want** AI-recommended secondaries  
**So that** I maximize my scoring potential

#### US-003: Meta Insights
**As a** list builder  
**I want to** see current faction win rates  
**So that** I can build competitive lists

### Acceptance Criteria

```gherkin
Feature: Match Prediction API

  Scenario: Predict match outcome
    Given I submit a prediction request
      | player1_faction | Necrons       |
      | player2_faction | Space Marines |
    When the API processes the request
    Then I should receive win probabilities for each player
    And the confidence score based on sample size
    And key matchup insights

  Scenario: Get secondary recommendations
    Given my faction is "Aeldari"
    And opponent faction is "Death Guard"
    And mission is "Take and Hold"
    When I request secondary recommendations
    Then I should receive ranked secondary objectives
    And expected success rates for each

  Scenario: Rate limit enforcement
    Given I am an anonymous user
    When I exceed 10 requests in an hour
    Then I should receive a 429 Too Many Requests
    And a message indicating upgrade options
```

---

## Implementation Estimate

| Phase | Effort | Dependencies |
|-------|--------|--------------|
| API Routes | 4 hours | FastAPI |
| Prediction Engine | 12 hours | Historical data |
| Secondary Recommender | 8 hours | Mission data |
| Rate Limiting | 3 hours | Redis |
| Documentation | 3 hours | OpenAPI |
| Testing | 4 hours | None |
| **Total** | **34 hours** | |

---

## References

- [Meta-Oracle Spec](file:///c:/Users/bfoxt/Vindicta-Platform/platform-core/specs/005-meta-oracle)
- [Arbiter-Predictor](file:///c:/Users/bfoxt/Vindicta-Platform/Arbiter-Predictor)
