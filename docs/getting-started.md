# Getting Started

## Installation

```bash
uv pip install git+https://github.com/vindicta-platform/Meta-Oracle.git
```

## Requirements

- Python 3.10+
- Gemini API key (for AI inference)

## Configuration

```bash
export GOOGLE_API_KEY=your-api-key
```

## First Prediction

```python
from meta_oracle import Oracle

oracle = Oracle()
result = oracle.predict(my_list, opponent_list)
```
