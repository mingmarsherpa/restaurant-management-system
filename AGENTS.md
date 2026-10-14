# AGENTS.md

## Project

Restaurant API built with Python 3.14, FastAPI, SQLAlchemy 2.x, asyncpg, and Alembic. Application code lives under `src/restaurant_api/`.

## Setup and Run

- Use the project virtual environment or `uv` for all Python commands.
- Install dependencies with `uv sync`.
- Set `DATABASE_URL` in `.env` before importing or running the application.
- Start the development server with `uv run uvicorn restaurant_api.main:app --reload`.
- Apply migrations with `uv run alembic upgrade head`.
- Create a migration with `uv run alembic revision --autogenerate -m "describe change"`, then review it manually.

## Code Guidelines

- Keep application code in `src/restaurant_api/` and preserve the existing package layout: models, schemas, router, configuration, and database setup.
- Use SQLAlchemy 2.x typed mappings with `Mapped` and `mapped_column` for new models.
- Use async database access consistently with `AsyncSession`; do not introduce synchronous database calls into request handlers.
- Store monetary values as integer paisa fields, following the existing `*_paisa` convention.
- Keep API request and response shapes in `schemas/`; keep persistence models in `models/`.
- Prefer relative imports within the `restaurant_api` package.
- Keep changes focused and avoid unrelated formatting or dependency upgrades.

## Database Changes

- Every model schema change must include a reviewed Alembic migration.
- Never edit an existing migration that may already have been applied; add a new migration instead.
- Check foreign-key delete behavior and relationship cascades explicitly.
- Do not commit credentials or local database files.

## Validation

- Run `uv run python -m compileall src` after Python changes.
- Run `uv run alembic check` when validating model and migration consistency.
- If tests are added, run them with `uv run pytest`.
- Inspect generated migrations before applying them to a shared database.
