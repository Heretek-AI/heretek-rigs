---
name: fastapi-async-development
description: Builds scalable FastAPI endpoints with Pydantic v2 schemas, async SQLAlchemy sessions, and comprehensive pytest fixtures.
---

# FastAPI Async Development Procedure

1. Read API specification and schema requirements.
2. Define request/response validation schemas using Pydantic v2 with strict typing.
3. Implement async route handlers using dependency injection (`Depends(get_db_session)`).
4. Author unit and integration tests using `pytest` and `httpx.AsyncClient`.
5. Run linting and formatting with Ruff: `ruff check .` and `ruff format --check .`.
6. Run strict static type checking: `mypy --strict app/`.
7. Execute test suite: `pytest --cov=app tests/`.
