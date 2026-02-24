# vindicta-oracle Development Guidelines

## Active Technologies
- Python 3.10+
- ollama (>=0.3), mcp (>=1.0.0), duckdb, diskcache
- FastAPI, Uvicorn, pytest-asyncio

## Project Structure
```text
src/vindicta_oracle/
tests/
```

## Commands
```powershell
uv run pytest
uv run ruff check src/
pre-commit run --all-files
```

## Code Style & Git Hygiene
- Strict async-first implementation for MCP servers
- **Git Hygiene**: All commits MUST be GPG-signed (`git commit -S`). Follow the global rules in `../../GEMINI.md`.
