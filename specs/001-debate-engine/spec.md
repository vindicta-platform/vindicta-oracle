# Specification: Debate Engine Foundation (v0.1.0)

**Feature ID:** 001-debate-engine
**Milestone:** v0.1.0 — Foundation
**Priority:** P0
**Status:** Specified
**Target Date:** Feb 24, 2026

---

## 1. Problem Statement

The Vindicta Platform's AI layer needs a debate-based decision system where
multiple specialist AI agents argue for different actions, and a judge agent
selects the best recommendation. Meta-Oracle provides this "council of AIs"
architecture. Without it, Primordia-AI would be a single-perspective engine
with no deliberative reasoning.

---

## 2. Vision

Create the DebateEngine framework with stub agents that can propose, argue
for, and adjudicate tactical actions through structured debate rounds.

---

## 3. User Stories

### US-01: Debate Engine — Multi-Agent Decision

> As the **Vindicta recommendation system**,
> I want to **run a structured debate between AI agents**,
> So that **the final recommendation considers multiple perspectives**.

**Acceptance Criteria:**

- [ ] `DebateEngine.debate(game_state)` returns `DebateResult`
- [ ] At least 2 agents propose actions
- [ ] Judge agent scores each proposal
- [ ] Winning proposal becomes the recommendation

### US-02: Agent Interface — Pluggable Agents

> As an **AI researcher**,
> I want to **implement custom debate agents via a protocol**,
> So that **I can experiment with different reasoning strategies**.

**Acceptance Criteria:**

- [ ] `DebateAgent` protocol with `propose()` and `argue()` methods
- [ ] Agents receive game state and debate context
- [ ] Stub agents provided as reference implementations
- [ ] Agent registration via DebateEngine configuration

### US-03: Debate Transcript — Audit Trail

> As the **Agent-Auditor-SDK**,
> I want to **record the full debate transcript**,
> So that **AI reasoning can be reviewed and analyzed**.

**Acceptance Criteria:**

- [ ] Each debate round produces a `DebateRound` entry
- [ ] Rounds include: proposals, arguments, scores, verdict
- [ ] Transcript serializable to JSON
- [ ] Timestamps on all entries

### US-04: Stub Agents — Reference Implementations

> As a **developer bootstrapping Meta-Oracle**,
> I want **pre-built stub agents** (aggressive, defensive, balanced),
> So that **the system can work end-to-end without ML models**.

**Acceptance Criteria:**

- [ ] `AggressiveAgent` — maximizes expected damage output
- [ ] `DefensiveAgent` — maximizes unit survivability
- [ ] `BalancedAgent` — weighted combination of both
- [ ] All agents use Primordia-AI evaluation as their base

---

## 4. Functional Requirements

### 4.1 DebateEngine

```python
from meta_oracle import DebateEngine, AggressiveAgent, DefensiveAgent

engine = DebateEngine(
    agents=[AggressiveAgent(), DefensiveAgent()],
    rounds=3,
    judge="scoring",  # scoring | llm | human
)

result = engine.debate(game_state)
print(result.winner.action)
print(result.transcript)
```

### 4.2 DebateAgent Protocol

```python
class DebateAgent(Protocol):
    name: str

    def propose(self, state: GameState) -> Proposal:
        """Propose an action with reasoning."""
        ...

    def argue(self, state: GameState, proposals: list[Proposal]) -> Argument:
        """Argue for own proposal or against others."""
        ...
```

### 4.3 DebateResult Model

| Field           | Type                | Description        |
| --------------- | ------------------- | ------------------ |
| `winner`        | `Proposal`          | Winning proposal   |
| `scores`        | `dict[str, float]`  | Agent name → score |
| `transcript`    | `list[DebateRound]` | Full debate log    |
| `total_time_ms` | `float`             | Debate duration    |

### 4.4 Stub Agent Behavior

| Agent      | Strategy              | Evaluation Weight                     |
| ---------- | --------------------- | ------------------------------------- |
| Aggressive | Maximize damage dealt | Material: 0.7, Position: 0.1, VP: 0.2 |
| Defensive  | Minimize damage taken | Material: 0.3, Position: 0.4, VP: 0.3 |
| Balanced   | Equal weighting       | Material: 0.4, Position: 0.3, VP: 0.3 |

---

## 5. Non-Functional Requirements

| Category          | Requirement                                      |
| ----------------- | ------------------------------------------------ |
| **Performance**   | 3-round debate < 500ms                           |
| **Dependencies**  | vindicta-core, primordia-ai                      |
| **Type Safety**   | 100% strict mypy                                 |
| **Extensibility** | New agents via Protocol, no inheritance required |

---

## 6. Out of Scope

- LLM-based agents (v0.2.0)
- Human-in-the-loop judging
- Agent training/learning

---

## 7. Success Criteria

| Metric            | Target                      |
| ----------------- | --------------------------- |
| Debate resolution | 3 rounds, 2+ agents         |
| Stub agents       | 3 reference implementations |
| Transcript        | Full audit trail            |
| Test coverage     | > 90%                       |
