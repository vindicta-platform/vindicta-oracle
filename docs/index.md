# Meta-Oracle

**AI-powered predictions through adversarial debate.**

Meta-Oracle uses a 5-agent swarm to analyze matchups, identify "sleeper" lists, and provide tactical predictions — all validated by the Rule-Sage auditor.

## How It Works

1. **Ingestion** — Tournament data loaded
2. **Debate** — Agents argue for/against outcomes
3. **Validation** — Rule-Sage checks all claims
4. **Prediction** — Council synthesizes result

## Installation

```bash
uv pip install git+https://github.com/vindicta-platform/Meta-Oracle.git
```

## Quick Prediction

```python
from meta_oracle import Oracle

oracle = Oracle()
result = oracle.predict(my_list, opponent_list)
print(f"Win Probability: {result.probability:.0%}")
```

---

[Full Platform](https://vindicta-platform.github.io/mkdocs/)
