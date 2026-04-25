# AI Incubator v2 Design

Date: 2026-04-25
Status: Approved design draft
Scope: v2 MVP usable loop

## 1. Current State

The current application is a full-stack MVP with FastAPI, PostgreSQL, React, React Flow, and OpenAI integration. It includes user auth, project CRUD, node CRUD, basic AI endpoints, and a React Flow based incubator page.

The current implementation has two structural issues:

- The mindmap is rendered as a generic node graph. Nodes are randomly positioned when no saved position exists, edges are generic, and the interface lacks the layout, curves, hierarchy, focus behavior, and editing feel of a real mind map.
- The AI layer is still framework-template driven. Users choose from fixed frameworks such as product manager, business canvas, technical feasibility, or Socratic. Most question generation is template lookup, which conflicts with the product goal of dynamic, user-led thinking.

v2 will replace the fixed framework flow with a general exploration system and replace the graph-like visual with a professional mindmap experience.

## 2. Product Goal

AI Incubator v2 should be a thinking workspace where users clarify vague ideas through continuous dialogue while watching their thinking become a structured mind map.

The primary interface is a dual-track workspace:

- Left side: continuous AI conversation. The AI asks one high-quality question at a time, summarizes user answers, and guides the thinking process.
- Right side: live mindmap. The map externalizes the user's thinking into questions, insights, assumptions, decisions, risks, and next steps.

Both sides are first-class inputs. A user can answer in the chat or click a map node and answer there. Both actions enter the same conversation history and update the same thinking state.

## 3. MVP Scope

The v2 MVP includes:

- Project creation without framework selection.
- A dual-panel workspace with chat and mindmap.
- A general AI thinking context instead of predefined frameworks.
- Real-time map updates based on user answers.
- Node selection and node-specific answering.
- AI-generated restructure suggestions requiring user confirmation.
- Basic persistence for messages, thinking nodes, map layout, and suggestions.

The v2 MVP excludes:

- Export to PDF, PNG, or Markdown.
- Version history comparison.
- Undo and redo beyond rejecting pending suggestions.
- Advanced search.
- Multi-user collaboration.
- Full professional mindmap editor parity.

## 4. Recommended Technical Route

Use a professional mindmap engine plus an AI state layer.

The current React Flow approach can be improved with ELK or Dagre, but it still leaves the product responsible for many mindmap-specific details: radial or bilateral tree layout, curved branch styling, node editing affordances, branch spacing, focus behavior, keyboard interaction, and export foundations.

For v2, evaluate Mind Elixir and SimpleMindMap. The initial MVP recommendation is Mind Elixir because it is framework-independent, simpler to wrap in React, and already provides mindmap-oriented rendering and editing behavior. SimpleMindMap remains a fallback if Mind Elixir cannot meet layout or interaction requirements.

The application must not bind business data directly to the chosen engine. Frontend code should use a neutral `ThinkingMap` shape and convert it through an adapter.

## 5. User Experience Design

The v2 workspace has four visible regions:

- Top bar: project title, save state, current thinking mode, pending restructure count, and navigation.
- Chat panel: AI and user messages, input box, loading state, and source markers showing which node or map area a message affects.
- Mindmap canvas: center idea and dynamically evolving branches.
- Node or suggestion panel: node details, answer affordance, and pending restructure suggestions.

The mindmap should feel like a real thinking map, not a flowchart. It should use curved branches, clear hierarchy, type-aware colors, status markers, automatic layout, zoom, pan, and current-node focus.

Node kinds:

- `idea`
- `question`
- `answer`
- `insight`
- `assumption`
- `decision`
- `risk`
- `next_step`

Node statuses:

- `open`
- `answered`
- `suggested`
- `confirmed`

AI can automatically add low-risk information, such as new questions, answer summaries, and insight nodes. High-risk structure changes require confirmation before changing the map.

High-risk changes include:

- Moving nodes.
- Merging nodes.
- Splitting nodes.
- Deleting nodes.
- Renaming established nodes.

## 6. AI Thinking Strategy

The AI should not use user-visible fixed frameworks. It should use a general system context that acts as a thinking partner.

The system context should combine a few stable creativity and questioning principles:

- Double Diamond: alternate between divergent exploration and convergent definition.
- Divergent and convergent thinking: generate breadth first when the idea is underdeveloped, then narrow when the structure becomes noisy.
- Geneplore: create tentative structures, inspect them, reinterpret them, and refine them.
- Socratic questioning: help the user inspect assumptions, evidence, alternatives, and implications.
- 5 Whys: use repeated why questions when the user is stuck on causes, but avoid mechanical repetition.
- How Might We: convert insights into open but bounded opportunity questions.
- SCAMPER-like prompts: use transformation questions when the user needs alternatives.

The AI's job is to ask, reflect, structure, and challenge. It should not take over the user's thinking or prematurely finalize a plan.

Core behavior rules:

- Ask only one main question per turn.
- Add at most one or two optional thinking angles when helpful.
- Do not make decisions for the user.
- Clearly separate facts, assumptions, insights, open questions, decisions, risks, and next steps.
- Avoid fixed industry templates as the visible product model.
- Use internal frameworks only as inspiration for better questions.
- Balance exploration with convergence.
- Suggest map restructures when the map becomes noisy, but require user confirmation.
- Use psychology-informed questioning only for creativity and thinking support, not therapy or diagnosis.

## 7. Thinking Mode Decision

The model should not decide divergent versus convergent mode by intuition alone. The backend should calculate project-state signals and provide a recommended mode to the model.

Example state signals:

```json
{
  "turn_count": 8,
  "node_count": 24,
  "answered_node_count": 10,
  "open_question_count": 7,
  "decision_count": 1,
  "assumption_count": 6,
  "risk_count": 3,
  "last_3_turns_repeated": false,
  "user_requested_action_plan": false,
  "user_expressed_confusion": true,
  "map_density": "high",
  "focused_node_depth": 2
}
```

Rule examples:

- First one to three turns default to divergent exploration unless the user asks for an action plan.
- Sparse information defaults to divergent exploration.
- Many branches without a clear definition defaults to convergence.
- Many open questions and high map density defaults to convergence or clarification.
- Multiple candidate solutions defaults to comparison and convergence.
- Clear assumptions without evidence defaults to validation.
- User asks for next steps defaults to convergence into minimum action.
- Repeated recent turns default to challenge, reframing, or a new angle.

The backend provides:

```json
{
  "recommended_mode": "converge",
  "reason": "There are many open questions and branches, but only one decision. The system should summarize before adding more branches."
}
```

The model must output its chosen mode and reason. If it overrides the recommendation, it must explain why.

## 8. AI Output Protocol

The AI service should return structured JSON rather than free text.

```json
{
  "thinking_mode": "diverge",
  "stage": "discover",
  "mode_reason": "The initial idea has too little context, so the next step is to explore user, motivation, and situation.",
  "assistant_message": "I see the broad direction. Before we shape it, I want to understand the situation where this idea matters.",
  "next_question": "Who would feel this problem most strongly, and what are they doing when it appears?",
  "question_intent": "Identify the first user context before discussing solutions.",
  "map_updates": [],
  "restructure_suggestions": [],
  "detected_gaps": [],
  "current_summary": {
    "facts": [],
    "assumptions": [],
    "insights": [],
    "open_questions": [],
    "decisions": [],
    "risks": []
  }
}
```

Valid `thinking_mode` values:

- `diverge`
- `converge`
- `clarify`
- `challenge`
- `validate`

Valid `stage` values:

- `discover`
- `define`
- `develop`
- `deliver`

The backend must validate this output before applying changes.

## 9. Frontend Architecture

Recommended frontend modules:

- `IncubatorWorkspacePage`: v2 workspace container.
- `ChatPanel`: message list, message source labels, input, submit state, retry affordance.
- `MindmapCanvas`: wrapper around the chosen mindmap engine.
- `mindmapAdapter`: converts `ThinkingMap` to the engine's format and converts engine events back to app events.
- `NodeInspector`: selected node detail, answer input, status, linked messages.
- `RestructureSuggestionPanel`: pending AI structure operations with accept and reject actions.
- `useIncubatorSession`: coordinates API calls, optimistic updates, refreshes, and error handling.

Neutral frontend data shape:

```ts
type ThinkingNode = {
  id: string
  parentId: string | null
  title: string
  kind:
    | 'idea'
    | 'question'
    | 'answer'
    | 'insight'
    | 'assumption'
    | 'decision'
    | 'risk'
    | 'next_step'
  status: 'open' | 'answered' | 'suggested' | 'confirmed'
  summary?: string
  sourceMessageIds: string[]
  children: ThinkingNode[]
}
```

The mindmap engine should never become the source of truth. It is a renderer and interaction layer. The backend and frontend store own the project state.

## 10. Backend Architecture

Keep FastAPI and SQLAlchemy. Add `/api/v2` instead of mutating v1 APIs in place.

Core models:

- `projects`: keep `title` and `status`; add `system_context_version`, `thinking_stage`, `thinking_mode`, and `summary_snapshot`. Keep legacy `framework` for compatibility but stop using it in v2.
- `conversation_messages`: stores all user and assistant messages, with optional `node_id`, `source`, `thinking_mode`, `stage`, and metadata.
- `thinking_nodes`: stores the v2 map, with `kind`, `status`, `title`, `summary`, `question`, `answer_summary`, `parent_id`, `sort_order`, `layout`, `source_message_ids`, and `confidence`.
- `restructure_suggestions`: stores pending and resolved structure operations.
- `incubator_runs`: stores AI orchestration inputs, outputs, validation results, model version, latency, and errors.

Primary APIs:

- `GET /api/v2/projects/{id}/workspace`
  - Returns project metadata, messages, thinking map, pending suggestions, and current mode.
- `POST /api/v2/projects/{id}/turns`
  - Accepts user input from chat or node context.
  - Returns user message, assistant message, updated map snapshot, pending suggestions, and current thinking mode.
- `POST /api/v2/restructure-suggestions/{id}/accept`
  - Applies approved operations.
- `POST /api/v2/restructure-suggestions/{id}/reject`
  - Marks suggestions rejected without changing the map.
- `PATCH /api/v2/thinking-nodes/{id}`
  - Updates user-editable node fields and layout metadata.

The AI output must pass schema validation and operation whitelisting before any database mutation.

## 11. Turn Processing Flow

Every user input follows one path:

1. Save the user message with `source` as `chat` or `node`.
2. Build a context package from the initial idea, recent messages, map summary, confirmed decisions, open questions, current node, and calculated state signals.
3. Calculate `recommended_mode` with rules.
4. Ask the model for a structured response.
5. Validate the response schema and operation list.
6. Save the assistant message.
7. Automatically apply low-risk map updates.
8. Save high-risk restructures as pending suggestions.
9. Return a synchronized workspace payload to the frontend.

Low-risk updates:

- Add a new child node.
- Update answer summary.
- Mark a question answered.
- Add a detected gap as an open question.

High-risk updates:

- Move node.
- Merge nodes.
- Split node.
- Delete node.
- Rename established node.

## 12. Error Handling

- If AI JSON parsing fails, save the user message, do not mutate the map, and return a recoverable assistant message or retry state.
- If the assistant message is valid but map updates fail validation, keep the text reply and discard invalid operations.
- If mindmap rendering fails, show a structured node-list fallback so the user can continue.
- If accepting a restructure fails, keep the suggestion pending and allow retry.
- If the network fails, keep the user input pending and allow resend.
- If the model times out, keep the input text and show a clear retry action.

Errors should be recorded in `incubator_runs` for debugging.

## 13. Testing Strategy

Backend unit tests:

- Thinking mode decision rules.
- AI output schema validation.
- Operation whitelist validation.
- Map update application.
- Suggestion accept and reject behavior.

Backend integration tests:

- `POST /turns` full flow with mocked AI.
- Node-originated answer updates both conversation and map.
- Invalid AI operations are rejected without corrupting state.

Frontend tests:

- Chat submit updates messages and map.
- Node click changes chat context.
- Node answer creates a synced message.
- Restructure accept and reject update UI correctly.
- Mindmap adapter converts `ThinkingMap` to engine data.
- Renderer fallback appears if the mindmap engine fails.

Manual acceptance:

- Start from a vague idea and complete eight to ten turns.
- The map should grow from a center idea into clear branches.
- Node answers should appear in the chat timeline.
- AI should propose restructuring when the map becomes noisy.
- Unconfirmed restructure suggestions should not mutate the map.

## 14. Migration Strategy

Use additive migration:

1. Add v2 tables and APIs.
2. Add a new v2 workspace page.
3. Keep current v1 project and node APIs running.
4. Change project creation to create v2 general incubator projects.
5. Hide framework selection after v2 is ready.
6. Retire v1 incubator only after the v2 loop is stable.

This avoids breaking the current MVP while allowing a deep redesign.

## 15. Implementation Order

1. Add v2 data models, migrations, schemas, and mocked turn API.
2. Build the v2 workspace shell with chat and a mindmap adapter.
3. Integrate the selected mindmap engine.
4. Implement the thinking mode decision service.
5. Implement the AI orchestrator with structured output validation.
6. Add low-risk map update application.
7. Add pending restructure suggestions and accept/reject flow.
8. Replace project creation and route users to the v2 workspace.
9. Add tests and manual acceptance coverage.

## 16. Open Decisions Resolved

- The v2 approach is a full redesign of the core experience, not a small patch.
- The interface uses dual-track chat and mindmap interaction.
- AI restructuring uses user confirmation for high-risk changes.
- The v2 MVP focuses on the usable thinking loop, not export, collaboration, or full editor features.
- The mindmap renderer should be a professional mindmap engine behind an adapter.
