# Implementation Plan: Debate Engine Foundation (v0.1.0)

**Spec Reference:** [spec.md](./spec.md)

---

## Proposed Changes

```
src/meta_oracle/
├── __init__.py
├── engine/
│   ├── __init__.py
│   └── debate_engine.py    # DebateEngine: orchestrate debate rounds
├── agents/
│   ├── __init__.py
│   ├── protocol.py         # DebateAgent protocol, Proposal, Argument
│   ├── aggressive.py       # AggressiveAgent stub
│   ├── defensive.py        # DefensiveAgent stub
│   └── balanced.py         # BalancedAgent stub
├── judging/
│   ├── __init__.py
│   └── scoring_judge.py    # Score-based winner selection
└── models/
    ├── __init__.py
    ├── debate_result.py    # DebateResult, DebateRound
    └── transcript.py       # Debate transcript serialization
```

### Tests

```
tests/
├── test_debate_engine.py    # Full debate flow
├── test_agents.py           # Stub agent behavior
├── test_judging.py          # Score-based judging
├── test_transcript.py       # Serialization round-trip
└── fixtures/
```

---

## Verification

```powershell
uv run pytest tests/ -v
uv run mypy src/meta_oracle/ --strict
```
