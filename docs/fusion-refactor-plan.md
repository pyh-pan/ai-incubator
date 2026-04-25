# Fusion Refactor Plan

Date: 2026-04-25
Status: Completed historical plan. The current implementation has been merged to `main`; use the README files and PRD for current project documentation.

## Goal

Fuse the useful parts of the local v2 branch and the GitHub source branch into a smaller, cleaner AI Incubator codebase. Preserve the current v2 product direction and functionality, while removing framework-management complexity and unsafe merge artifacts.

## Source Lines

- `feature/ai-incubator-v2`: primary product and architecture base. It contains the dual-panel workspace, `/api/v2`, structured thinking models, orchestrator, map updates, suggestions, and current passing test baseline.
- `github-check/main`: selective donor branch. It contains mature auth handling, `/api` contract behavior, provider/fallback ideas, UI stability fixes, and historical Playwright coverage, but also includes committed artifacts and deferred framework features.
- local `main`: staging line for docs and repository hygiene only. Do not use it as the product base for the refactor.

## Product Boundary

Keep one fixed general thinking framework. Do not restore user-visible framework selection, framework editing, framework APIs, framework snapshots, or settings-driven custom prompts.

Project creation should stay simple: title plus optional background. The workspace should be the center of the product: chat, mindmap, node inspector, and user-confirmed restructure suggestions.

## Keep

- v2 workspace route and components: `IncubatorWorkspacePage`, `ChatPanel`, `MindmapCanvas`, `NodeInspector`, `RestructureSuggestionPanel`, `useIncubatorSession`.
- v2 backend state model: conversation messages, thinking nodes, restructure suggestions, AI run records.
- deterministic AI fallback for tests and local development.
- current v2 tests for schemas, mode selection, map operations, orchestrator, API, auth, and frontend adapter behavior.
- concise `AGENTS.md` plus `docs/project-archive.md`.

## Port From GitHub Source

- Real JWT dependency path: `HTTPBearer(auto_error=False)`, token decode, `get_current_user_id`, and working `/auth/me`.
- Auth API polish: duplicate username checks, token response including user, consistent `401` responses.
- Project ownership checks on protected project routes.
- AI provider hygiene: OpenAI/GLM selection, no external call unless configured, short timeout, no retries in request path.
- Selected UI fixes: responsive project list modal, navigate to workspace after project creation, stable relative time helper if still useful.
- Selected E2E scenarios: auth flow, project creation, workspace load, submit answer/turn, suggestion accept/reject. Recreate clean tests rather than copying old bulky suites.

## Drop

- `Framework` model, API, service, schemas, settings page, settings store, framework prompt editing, and framework recommendation flow.
- Legacy fixed framework templates except a small internal generic prompt/context if needed.
- Old v1 `IncubatorPage` as a primary product surface. Mine only small visual or interaction details if they directly improve v2.
- Remote artifacts: `node_modules`, `.claude`, `.playwright-mcp`, screenshots, network logs, old generated reports, personal metadata.
- Long `CLAUDE.md` history. Keep only the compressed archive already moved to `docs/project-archive.md`.

## Target Architecture

Backend should expose one stable API surface under `/api`. Legacy routes can remain only where the frontend or tests still need them, but new workspace behavior should live under `/api/v2`.

Authentication should be real across project and workspace routes. No route should use placeholder user IDs.

The AI layer should have one generic thinking contract:

- build state signals from project, messages, and nodes;
- choose or recommend a thinking mode;
- call a configured provider only when credentials exist;
- validate structured output;
- apply low-risk node creation directly;
- store high-risk structure edits as pending suggestions.

Frontend should treat the mindmap renderer as a view layer, not the source of truth. `ThinkingMap`/`ThinkingNode` remains the neutral app model, with adapters converting to renderer-specific structures.

## Refactor Phases

### Phase 1: Isolate and Baseline

Create a fresh worktree from `feature/ai-incubator-v2`, for example `.worktrees/clean-v2-fusion` on `integration/clean-v2-fusion`.

Run the current baseline:

- backend pytest without coverage overrides;
- frontend Vitest;
- frontend build.

Record any pre-existing failures before making changes.

### Phase 2: Auth and Ownership

Port real JWT auth from `github-check/main` into the v2 base. Replace placeholder project user lookup with `Depends(get_current_user_id)`.

Add or update tests for:

- register/login response includes `user`;
- duplicate email and username rejection;
- `/auth/me` returns current user;
- missing token returns `401`;
- users cannot access each other's projects or v2 workspace.

### Phase 3: Simplify Project Creation

Remove user-visible framework fields from schemas, frontend forms, and project creation flow. Keep `framework="general"` only if needed for legacy compatibility.

Support optional project background text if the v2 workspace can use it without adding UI complexity.

After creation, navigate directly into `/projects/:projectId`.

### Phase 4: AI Service Cleanup

Replace framework-heavy AI service paths with a generic provider helper and deterministic fallback.

Keep provider configuration low-level and environment-driven. Do not add a settings page unless the user later asks for runtime provider editing.

Ensure tests can run without `OPENAI_API_KEY`, `GLM_API_KEY`, or network access.

### Phase 5: Frontend Consolidation

Make `IncubatorWorkspacePage` the only active project workspace route. Remove or quarantine old `IncubatorPage` code after confirming no active imports depend on it.

Keep project list dense and simple. Remove framework tags or replace them with neutral status/context display.

Review component boundaries and split only where it reduces actual complexity:

- API calls stay in `frontend/src/api/incubator.ts`;
- orchestration state stays in `useIncubatorSession`;
- display-only widgets stay in `components/incubator`.

### Phase 6: Migrations and Repository Hygiene

Create a clean migration path for the selected v2 model. Do not import remote framework migrations.

Keep `.gitignore` strict for worktrees, local tool state, databases, coverage, Playwright output, build output, and dependency folders.

Do not copy remote committed artifacts into the final branch.

### Phase 7: Critical E2E Coverage

Rebuild a small Playwright suite around current behavior:

- user can register/login;
- user can create a project;
- workspace loads root idea and chat;
- user can submit a turn and see chat/map update;
- pending restructure suggestion can be accepted or rejected if generated.

Avoid restoring the historical broad Playwright matrix unless a specific regression justifies it.

## Review Gates

After each phase, run the narrow tests for that phase and commit a focused change. Before final integration, run:

- `cd backend && python -m pytest -q -o addopts=''`
- `cd frontend && npm test -- --run`
- `cd frontend && npm run build`

Run Playwright only after backend and frontend can start cleanly.

## Key Risks

- Migration drift between local v2 and remote GitHub migrations. Mitigation: manually design the final migration path and exclude framework migrations.
- Accidental resurrection of framework complexity. Mitigation: reject schema/UI/API fields whose only purpose is framework customization.
- Auth changes breaking tests that relied on placeholder users. Mitigation: update fixtures to create users and pass real tokens.
- Old v1 workspace code hiding useful behavior. Mitigation: inspect before deleting, but port only direct improvements.

## Open Decisions

1. Whether optional project background text should be kept in the simplified creation form.
2. Whether provider/API key configuration should remain environment-only for now.
3. Whether to remove old v1 APIs immediately or keep them temporarily for compatibility while v2 stabilizes.

Recommended defaults: keep optional background text, keep provider configuration environment-only, and keep legacy APIs temporarily but unused by the active frontend.
