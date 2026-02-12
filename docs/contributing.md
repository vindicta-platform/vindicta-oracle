# Contributing

## Pre-Commit Hooks (Required)

All contributors **must** install and run pre-commit hooks before committing.
```bash
uv pip install pre-commit
pre-commit install
```

## Setup

```bash
git clone https://github.com/vindicta-platform/Meta-Oracle.git
cd Meta-Oracle
uv venv && uv pip install -e ".[dev]"
pytest tests/ -v
```

MIT License
