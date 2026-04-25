# AI Incubator Frontend

React + TypeScript frontend for the AI Incubator workspace.

## Tech Stack

- React 19 + TypeScript
- Vite 7
- React Router 7
- TanStack Query 5
- Zustand 5
- Ant Design 6
- MindElixir 5 for the thinking map
- TailwindCSS 3
- Axios
- Vitest + React Testing Library

## Quick Start

```bash
npm install
cp .env.example .env
npm run dev
```

The default API base is `http://localhost:8000/api`.

## Scripts

- `npm run dev` - start the Vite dev server.
- `npm run build` - run TypeScript build and create a production bundle.
- `npm run lint` - run ESLint.
- `npm test -- --run` - run the unit test suite once.
- `npm run test:ui` - open Vitest UI.
- `npm run test:coverage` - run coverage.

## Routes

- `/` - landing page.
- `/login` - login.
- `/register` - registration.
- `/projects` - authenticated project list.
- `/projects/:projectId` - authenticated v2 incubation workspace.

## Source Layout

```text
frontend/
├── src/
│   ├── api/                  # Axios client and API wrappers
│   ├── components/incubator/  # Workspace panels and map adapter
│   ├── components/ui/         # Shared layout
│   ├── hooks/                 # Workspace session hook
│   ├── pages/                 # Route pages
│   ├── stores/                # Zustand stores
│   ├── test/                  # Vitest setup and tests
│   ├── types/                 # Shared TypeScript types
│   ├── App.tsx
│   └── main.tsx
└── package.json
```

## Workspace Behavior

The workspace is a three-pane tool surface:

- `ChatPanel` sends chat or node-scoped turns to `/api/v2/projects/:id/turns`.
- `MindmapCanvas` renders `ThinkingNode` data with MindElixir. Node topics use concise titles; full questions and summaries stay in the inspector.
- `NodeInspector` shows the selected node details.
- `RestructureSuggestionPanel` lets users accept or reject pending high-risk map changes.

The frontend does not expose multiple thinking frameworks. Project creation accepts a title and optional background text, then navigates directly into the workspace.
