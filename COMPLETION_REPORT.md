# AI Incubator Current Implementation Summary

Last updated: 2026-04-26

This file summarizes the current implementation state. Historical completion notes from the earlier React Flow and multi-framework version are no longer active project documentation.

## Product State

AI Incubator is a full-stack v2 workspace for clarifying ideas through AI-guided questions and a visual thinking map. The active product direction is:

- one fixed general thinking approach;
- no user-visible framework selection or framework editing;
- chat-first incubation with structured map updates;
- deterministic fallback behavior when external AI providers are not configured.

## Implemented Backend

- JWT authentication with register, login, and `/auth/me`.
- Authenticated project CRUD with ownership checks.
- Compatibility endpoints for legacy projects, nodes, and `/api/ai`.
- V2 workspace API:
  - `GET /api/v2/projects/{project_id}/workspace`
  - `POST /api/v2/projects/{project_id}/turns`
  - `POST /api/v2/restructure-suggestions/{suggestion_id}/accept`
  - `POST /api/v2/restructure-suggestions/{suggestion_id}/reject`
- V2 persistence for conversation messages, thinking nodes, restructure suggestions, and AI runs.
- AI provider helpers for OpenAI and GLM.
- V2 orchestrator with schema validation, low-value output detection, duplicate question detection, and deterministic fallbacks.

## Implemented Frontend

- Landing, login, register, project list, and v2 workspace routes.
- Project creation with title and optional background information.
- Automatic navigation into `/projects/:projectId` after creation.
- Workspace layout with:
  - chat panel;
  - MindElixir map canvas;
  - node inspector;
  - pending restructure suggestion panel.
- Zustand auth store and TanStack Query-backed API calls.

## Active Source Areas

```text
backend/app/api/v2.py
backend/app/services/incubator_orchestrator.py
backend/app/services/question_strategy.py
backend/app/services/thinking_mode_service.py
backend/app/services/map_update_service.py
frontend/src/pages/IncubatorWorkspacePage.tsx
frontend/src/components/incubator/
frontend/src/hooks/useIncubatorSession.ts
frontend/src/api/incubator.ts
```

## Verification Baseline

Use these commands after behavior changes:

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

Recent verification after the remote-fix fusion:

- Backend: 67 tests passed.
- Frontend lint: passed.
- Frontend unit tests: 5 passed.
- Frontend production build: passed.

## Deferred Ideas

- User-visible multi-framework selection.
- Runtime framework prompt editing.
- Broad Playwright matrix from the old prototype.
- Export, collaboration, and sharing workflows.
- Runtime provider configuration UI.
