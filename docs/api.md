# API

## Oracle

```python
from meta_oracle import Oracle

oracle = Oracle()
result = oracle.predict(my_list, opponent_list, mission="Purge the Enemy")
```

## PredictionResult

```python
class PredictionResult:
    probability: float  # 0.0 to 1.0
    confidence: float   # margin of error
    factors: list[str]  # key factors
```

## Sleeper Detection

```python
sleepers = oracle.find_sleepers(faction="Tyranids")
```
