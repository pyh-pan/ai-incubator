# AI Incubator Product Requirements

Last updated: 2026-04-26

## 1. Product Direction

AI Incubator helps users turn vague ideas into clearer, more actionable concepts. It should make the user's thinking visible through questions, conversation, and a thinking map. It should not replace the user's judgment with generated conclusions.

The current product uses one fixed general thinking approach. It must not expose multiple framework choices, custom framework editing, or settings-heavy prompt workflows unless that direction is explicitly reopened.

## 2. Target Users

- Founders and product builders refining early product ideas.
- Researchers shaping questions, assumptions, and validation paths.
- Creators developing concepts, stories, or projects.
- Students structuring topics and next steps.
- Independent learners planning personal goals.

## 3. Core User Journey

1. User registers or logs in.
2. User creates a project with a title and optional background.
3. App opens the incubation workspace.
4. AI asks one focused question at a time.
5. User answers through chat or around a selected node.
6. The thinking map updates with concise nodes.
7. High-risk map restructuring is shown as a suggestion and requires user confirmation.

## 4. Current Feature Requirements

### Project Creation

- Required: idea title.
- Optional: background information such as target users, constraints, current assumptions, or open questions.
- Do not ask the user to choose a thinking framework.
- After creation, navigate directly to `/projects/:projectId`.

### Workspace

The workspace is the primary product surface and contains:

- `ChatPanel` for conversation and node-scoped turns.
- `MindmapCanvas` for visualizing thinking nodes with MindElixir.
- `NodeInspector` for full node details, including questions and summaries.
- `RestructureSuggestionPanel` for accepting or rejecting pending structural changes.

The map should show concise titles. Full questions, summaries, and answer context belong in the inspector or chat.

### AI Behavior

- Ask one main question per turn.
- Use internal thinking modes: `diverge`, `converge`, `clarify`, `challenge`, and `validate`.
- Do not show fixed framework names to users.
- Separate facts, assumptions, insights, questions, decisions, risks, and next steps when possible.
- Reject or replace low-value generic questions such as "还有什么需要补充？".
- Avoid duplicate follow-up questions.
- Use deterministic fallback output when the provider is not configured, returns invalid JSON, or returns low-quality output.

### Map Updates

- Low-risk node creation can be applied directly.
- High-risk operations such as moving, renaming, merging, splitting, or deleting nodes require explicit user confirmation through restructure suggestions.
- Map renderer state is not the source of truth; backend `ThinkingNode` records are.

### Authentication and Ownership

- Missing or invalid credentials return `401`.
- Users can only access their own projects and v2 workspaces.
- Register and login return both an access token and user payload.

## 5. Technical Requirements

### Backend

- FastAPI API server.
- SQLAlchemy models and Alembic migrations.
- PostgreSQL for normal development and SQLite for tests.
- JWT auth.
- OpenAI-compatible client for OpenAI and GLM.
- Pydantic schema validation for AI output.

Current v2 tables:

- `conversation_messages_v2`
- `thinking_nodes`
- `restructure_suggestions`
- `incubator_runs`

Legacy compatibility tables can remain while old endpoints exist:

- `mindmap_nodes`
- `conversation_history`
- `evolution_history`

### Frontend

- React + TypeScript + Vite.
- React Router authenticated routes.
- TanStack Query for server state.
- Zustand for auth state.
- MindElixir for map rendering.
- Ant Design and TailwindCSS for UI.

## 6. Testing Requirements

- Backend tests cover auth, ownership, v2 schemas, map operation validation, thinking mode selection, AI fallback behavior, and v2 API responses.
- Frontend tests cover stores and map data adapters.
- Full verification before shipping:

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

## 7. Deferred Scope

- User-visible framework selection.
- Custom framework prompt editing.
- Runtime provider/API-key settings UI.
- Collaboration and sharing.
- Export to PDF, image, or structured reports.
- Large Playwright suite beyond critical user journeys.
