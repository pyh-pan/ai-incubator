# AI Incubator

AI Incubator is a full-stack idea incubation workspace. It helps users clarify vague ideas through focused AI questions, a visual thinking map, and a structured conversation history.

The current product direction is intentionally simple: one fixed general thinking approach, no user-visible framework picker, and deterministic fallback behavior when external AI providers are unavailable.

## Current Capabilities

- Email/password authentication with JWT bearer tokens.
- Project creation with a title and optional background context.
- A v2 incubation workspace at `/projects/:projectId` with:
  - chat-based thinking turns;
  - MindElixir-powered thinking map visualization;
  - node inspector for full question and summary details;
  - pending restructure suggestions that require user acceptance.
- Provider-aware AI calls for OpenAI or GLM, with local fallback output for development and tests.
- Backend and frontend regression tests for auth, v2 API contracts, map updates, fallback behavior, and frontend adapters/stores.

## Project Structure

```text
ai-incubator/
├── AGENTS.md                 # Contributor and agent workflow rules
├── backend/                  # FastAPI, SQLAlchemy, pytest
├── frontend/                 # React, Vite, MindElixir, Vitest
├── docs/
│   ├── prd/PRD.md            # Current product requirements
│   ├── fusion-refactor-plan.md
│   └── project-archive.md    # Historical notes, not active instructions
└── README.md
```

## Tech Stack

### Frontend

- React 19 + TypeScript
- Vite 7
- React Router 7
- TanStack Query 5
- Zustand 5
- Ant Design 6
- MindElixir 5
- TailwindCSS 3
- Axios
- Vitest + React Testing Library

### Backend

- FastAPI 0.115
- Python 3.11+ with Python 3.13-compatible dependencies
- SQLAlchemy 2
- PostgreSQL in normal development; SQLite is used by tests
- Alembic migrations
- OpenAI-compatible client for OpenAI and GLM
- JWT auth with `python-jose`
- pytest

## Quick Start

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

API docs: http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Frontend dev server: http://localhost:5173

## Test Commands

```bash
cd backend
DATABASE_URL=sqlite:///./baseline_test.db .venv/bin/python -m pytest -q -o addopts=''
```

```bash
cd frontend
npm run lint
npm test -- --run
npm run build
```

## Documentation

- [AGENTS.md](./AGENTS.md) - durable contributor and agent rules.
- [Backend README](./backend/README.md) - backend setup, API surface, and services.
- [Frontend README](./frontend/README.md) - frontend setup and UI structure.
- [PRD](./docs/prd/PRD.md) - current product requirements.
- [Current implementation summary](./COMPLETION_REPORT.md) - shipped capabilities and verification baseline.
- [Fusion refactor plan](./docs/fusion-refactor-plan.md) - completed historical merge plan.
- [Project archive](./docs/project-archive.md) - historical context and deferred ideas.
- [V2 design draft](./docs/superpowers/specs/2026-04-25-ai-incubator-v2-design.md) - historical v2 design artifact.
- [V2 implementation plan](./docs/superpowers/plans/2026-04-25-ai-incubator-v2.md) - historical implementation plan.
- [Remote fixes fusion plan](./docs/superpowers/plans/2026-04-26-remote-fixes-v2-fusion.md) - completed historical fusion plan.
