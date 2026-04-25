# AI Incubator Backend

FastAPI backend for authentication, project management, legacy node APIs, and the current v2 incubation workspace.

## Tech Stack

- FastAPI 0.115
- SQLAlchemy 2
- Alembic 1.13
- PostgreSQL for normal development
- SQLite for tests
- Pydantic 2
- JWT auth with `python-jose`
- OpenAI-compatible client for OpenAI and GLM
- pytest

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs are available at http://localhost:8000/docs.

## Environment

Required for normal development:

- `DATABASE_URL` - PostgreSQL connection string.
- `SECRET_KEY` - JWT signing key.

Optional AI provider settings:

- `AI_PROVIDER=openai` or `AI_PROVIDER=glm`
- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `GLM_API_KEY`
- `GLM_API_BASE`
- `GLM_MODEL`

If provider credentials are missing or still use placeholder values, v2 AI flows use deterministic fallback behavior.

## API Surface

Routers are registered both at legacy root paths and under `/api` for compatibility. The frontend uses `/api`.

### Auth

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`

### Projects

- `POST /api/projects` - create a project with `title` and optional `more_info`.
- `GET /api/projects`
- `GET /api/projects/{project_id}`
- `PUT /api/projects/{project_id}`
- `DELETE /api/projects/{project_id}`
- `GET /api/projects/{project_id}/mindmap` - legacy node tree endpoint.

### Legacy AI Compatibility

- `POST /api/ai/recommend-framework` - compatibility endpoint; returns `general`.
- `POST /api/ai/generate-question`
- `POST /api/ai/extract-points`
- `POST /api/ai/followup/{node_id}`

### V2 Incubator

- `GET /api/v2/projects/{project_id}/workspace`
- `POST /api/v2/projects/{project_id}/turns`
- `POST /api/v2/restructure-suggestions/{suggestion_id}/accept`
- `POST /api/v2/restructure-suggestions/{suggestion_id}/reject`

## Source Layout

```text
backend/
├── app/
│   ├── api/                  # FastAPI routers
│   ├── core/                 # config, database, auth helpers, time helpers
│   ├── models/               # SQLAlchemy models
│   ├── schemas/              # Pydantic request/response schemas
│   ├── services/             # AI, orchestration, map updates, mode selection
│   └── main.py
├── alembic/                  # migrations
├── tests/                    # pytest suite
├── requirements.txt
├── pyproject.toml
└── pytest.ini
```

## Core Services

- `ai_service.py` - provider/client helpers and legacy `/api/ai` compatibility.
- `incubator_orchestrator.py` - v2 turn orchestration, AI JSON validation, fallback handling, and AI run logging.
- `question_strategy.py` - internal fallback question strategy and low-value question detection.
- `thinking_mode_service.py` - chooses `diverge`, `converge`, `clarify`, `challenge`, or `validate` from workspace signals.
- `map_update_service.py` - validates and applies map operations.

## Data Model

Current workspace tables:

- `users`
- `projects`
- `conversation_messages_v2`
- `thinking_nodes`
- `restructure_suggestions`
- `incubator_runs`

Legacy compatibility tables still exist for old APIs:

- `mindmap_nodes`
- `conversation_history`
- `evolution_history`

`projects.framework` remains as a compatibility field and defaults to `general`; it is not a user-visible framework selection feature.

## Tests

```bash
DATABASE_URL=sqlite:///./baseline_test.db .venv/bin/python -m pytest -q -o addopts=''
```

Useful targeted examples:

```bash
.venv/bin/python -m pytest tests/test_v2_api.py -q -o addopts=''
.venv/bin/python -m pytest tests/test_incubator_orchestrator.py -q -o addopts=''
.venv/bin/python -m pytest tests/test_question_strategy.py -q -o addopts=''
```
