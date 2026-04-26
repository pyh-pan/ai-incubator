# Dual Agent Mindmap Workspace Design

## Product Goal

AI Incubator should help users turn an initial idea and background information into a visible, evolving thinking map. The AI should not rush into shallow one-question-at-a-time chat. It should first understand whether the project context is sufficient, ask for missing background when needed, then generate multiple high-quality thinking questions that become XMind-style map nodes. Users can answer through the conversation panel or directly on map nodes, and the system keeps both views synchronized.

## Confirmed Direction

- Workspace uses a two-column layout.
- Left column is a narrower conversation and input surface, defaulting to about 340px and resizable by drag.
- Right column is the primary XMind Clean mind map canvas.
- The current right-side details column is removed.
- Node details are shown in popovers anchored to map nodes.
- Initial AI output is not a single question. It is either a background-completion question batch or a dynamic batch of 3-5 deeper thinking questions.
- Background-completion questions appear in the left conversation but are consolidated into the center node, not rendered as ordinary map child nodes.
- Ordinary question nodes represent high-value thinking directions.
- Users can answer through a node popover or by batch-answering multiple questions in the left conversation.
- The product uses two internal agents: a Thinking Agent and a Map Agent.

## Visual Direction

The mind map should follow the selected "XMind Clean" direction:

- Light background.
- White rounded nodes.
- Soft curved connectors.
- A larger center node with stronger emphasis.
- Subtle shadows and restrained color accents.
- Clear selected/open/answered/needs-context states.
- No decorative gradients, no visual clutter, and no extra inspector column.

Node state styling:

- `open`: blue border.
- `answered`: green or muted confirmed state.
- `needs_context`: amber border.
- `selected`: stronger border and shadow.
- `resolved`: quiet gray state.

## Layout

```text
┌─────────────────────────┬──────────────────────────────────────────────┐
│ Conversation             │ XMind Clean mind map canvas                 │
│ default 340px            │ remaining width                             │
│ resizable                │ center node + question/follow-up hierarchy  │
└─────────────────────────┴──────────────────────────────────────────────┘
```

The left column contains:

- Collapsible AI thinking summaries.
- Background-completion question batches.
- Thinking question batches.
- User answer records.
- Automatic answer-to-node match confirmations.
- Bottom input for free-form additions or batch answers.

The right canvas contains:

- A center node summarizing the user's initial idea and background.
- First-level question nodes generated from the center node.
- Follow-up nodes generated from answered question nodes.
- Popovers for center-node background and ordinary-node answering.

## Center Node

The center node is special. It is the single source of truth for the user's starting context.

Center node popover contains:

- Original idea.
- Background information summary.
- Known facts.
- Assumptions.
- Constraints.
- Target users.
- Desired outcomes.
- Unresolved context gaps.
- A background supplement input.

Updating the center node with background information does not create ordinary child nodes by itself. It updates project context. Once context is sufficient, the Thinking Agent can generate ordinary thinking question nodes.

## Ordinary Question Node

Each question node contains:

- `title`: short map label.
- `question`: full AI question.
- `rationale`: why this question matters.
- `expected_answer_type`: what kind of answer would be useful.
- `answer_summary`: summary of the user's answer after answered.
- `status`: `open`, `answered`, `needs_context`, or `resolved`.
- `parent_id`: center node or another question node.
- `source_message_ids`: linked conversation messages.

Ordinary node popover contains:

- Short title.
- Full question.
- Rationale.
- Expected answer type.
- Parent context summary.
- Answer input.
- Confirm answer action.

Confirming an answer marks the node answered and triggers focused follow-up generation.

## Dual Agent Architecture

The backend coordinates two internal AI responsibilities. These may be two model calls or two schema-constrained passes, but they must remain logically separate.

### Thinking Agent

The Thinking Agent decides what should be asked and why. It does not directly mutate map state.

Responsibilities:

- Build understanding from the full workspace context.
- Judge whether background context is sufficient.
- If insufficient, ask 3-6 structured background-completion questions.
- If sufficient, generate dynamic 3-5 high-quality thinking questions across meaningful directions.
- For answered nodes, generate 1-3 focused follow-up questions or mark the branch resolved.
- Produce a concise user-visible reasoning summary.
- Produce backend audit notes that are not shown in the UI.

The Thinking Agent must avoid generic filler such as "还有什么需要补充？". When it lacks enough context, it should ask specific background-completion questions before generating deeper thinking questions.

### Map Agent

The Map Agent translates thinking and user answers into durable workspace structure. It does not invent new strategic questions beyond the Thinking Agent's output.

Responsibilities:

- Consolidate user-provided idea and background into center-node context.
- Convert Thinking Agent question batches into concise map nodes.
- Attach full question details, rationale, and expected answer types to node metadata.
- Mark nodes answered when user answers them.
- Route node-scoped answers back to the Thinking Agent with parent chain context.
- Convert follow-up questions into child nodes.
- Generate conversation events that keep the left panel synchronized.

### Deterministic Application Logic

The app, not the model, owns:

- Authentication and ownership.
- Database writes.
- Schema validation.
- Operation risk checks.
- Node status transitions.
- Rendering state.
- Fallback behavior when model output fails validation.

## Workspace Context

Every AI turn uses an explicit backend-built context package:

```ts
WorkspaceContext {
  project: {
    id: string
    title: string
    original_idea: string
    background_summary: string | null
    known_facts: string[]
    assumptions: string[]
    constraints: string[]
    target_users: string[]
    desired_outcomes: string[]
    unresolved_context_gaps: string[]
    context_sufficiency: "unknown" | "insufficient" | "sufficient"
  }
  map_state: {
    center_node: CenterNodeContext
    open_question_nodes: QuestionNodeContext[]
    answered_nodes: QuestionNodeContext[]
    focused_node?: QuestionNodeContext
  }
  recent_conversation: ConversationContextItem[]
  user_input: {
    source: "chat" | "node"
    content: string
    answered_node_ids: string[]
  }
}
```

The backend should log enough of this context in `incubator_runs` to debug why the AI asked a given question.

## Thinking Agent Output

```ts
ThinkingOutput {
  context_sufficiency: "insufficient" | "sufficient"
  background_questions?: BackgroundQuestion[]
  thinking_questions?: ThinkingQuestion[]
  follow_up_questions?: FollowUpQuestion[]
  answer_matches?: AnswerMatch[]
  reasoning_trace: {
    visible_summary: string
    audit_notes: Record<string, unknown>
  }
}

BackgroundQuestion {
  question: string
  why_needed: string
  expected_signal: string
}

ThinkingQuestion {
  question: string
  short_title: string
  why_this_matters: string
  expected_answer_type: string
}

FollowUpQuestion {
  parent_question_id: string
  question: string
  short_title: string
  why_this_matters: string
  expected_answer_type: string
}

AnswerMatch {
  node_id: string
  extracted_answer: string
  confidence: "high" | "medium" | "low"
}
```

Rules:

- If context is insufficient, return 3-6 `background_questions` and no ordinary `thinking_questions`.
- If context is sufficient and this is a broad project turn, return 3-5 `thinking_questions`.
- If the user answered a focused node, return 1-3 `follow_up_questions` or no follow-ups with a resolved recommendation.
- `visible_summary` is shown to users in a collapsible thinking block.
- `audit_notes` stays backend-only.

## Map Agent Output

```ts
MapOutput {
  center_node_patch?: {
    title: string
    idea_summary: string
    background_sections: {
      known_facts: string[]
      assumptions: string[]
      constraints: string[]
      target_users: string[]
      desired_outcomes: string[]
    }
    unresolved_context_gaps: string[]
    context_sufficiency: "insufficient" | "sufficient"
  }
  node_operations: MapOperation[]
  conversation_events: ConversationEvent[]
  pending_answer_match?: PendingAnswerMatch
}

MapOperation {
  type:
    | "create_question_node"
    | "create_followup_node"
    | "mark_answered"
    | "mark_resolved"
  parent_id?: string
  node_id?: string
  title?: string
  detail_question?: string
  rationale?: string
  expected_answer_type?: string
  answer_summary?: string
  status?: "open" | "answered" | "needs_context" | "resolved"
}
```

The backend applies only validated operations. High-risk structural edits are still suggestions requiring explicit confirmation.

## Workflow

### 1. Project Creation

User creates a project with an idea title and optional background. The backend persists the project and opens the workspace.

### 2. First Workspace Load

Backend builds `WorkspaceContext`.

If context is insufficient:

- Thinking Agent returns 3-6 background questions.
- Map Agent updates the center context with known information and context gaps.
- Left conversation displays a background-completion question batch.
- Right map displays only the center node.

If context is sufficient:

- Thinking Agent returns 3-5 thinking questions.
- Map Agent creates first-level question nodes.
- Left conversation displays a question batch.
- Right map displays center node plus question nodes.

### 3. Background Completion

User answers background-completion questions in the left panel.

The backend sends the answer through the dual-agent flow:

- Map Agent consolidates the answer into center context.
- Thinking Agent reassesses sufficiency.
- If still insufficient, another background batch may appear.
- If sufficient, a 3-5 question batch is generated.

### 4. Node Answer

User clicks a question node, reads the popover, enters an answer, and confirms.

Backend flow:

- Mark the parent node answered.
- Add answer summary to the node.
- Send node, parent chain, center context, and answer to Thinking Agent.
- Generate 1-3 follow-up child questions or resolve the branch.
- Map Agent creates child nodes and conversation events.

### 5. Left-Panel Batch Answer

User can answer several visible questions in one left-panel message.

Backend flow:

- Thinking Agent extracts possible node-answer matches.
- High-confidence matches are applied.
- Medium-confidence or multi-node matches produce a lightweight confirmation object.
- Low-confidence content becomes a center-context supplement and may trigger background reassessment.

The UI shows a confirmation block when needed, such as:

> I think this answered: Target users, Core experience, Quality boundary. Confirm?

After confirmation, the backend applies matches and triggers follow-ups for each answered node.

### 6. Collapsible Thinking Trace

When AI is working, the left panel displays a gray thinking block.

When complete:

- The block collapses automatically.
- It shows a concise summary line.
- Users can expand it to see `visible_summary`.
- The UI never displays raw model chain-of-thought or backend-only `audit_notes`.

## API Design

Keep existing v2 routes where useful and add explicit node-answer and match-confirm routes:

- `GET /api/v2/projects/{project_id}/workspace`
  - Returns center context, messages, nodes, suggestions, and pending match confirmations.
- `POST /api/v2/projects/{project_id}/turns`
  - Handles left-panel free-form input and batch answers.
- `POST /api/v2/projects/{project_id}/nodes/{node_id}/answer`
  - Handles node popover answers.
- `POST /api/v2/answer-matches/{match_id}/confirm`
  - Confirms uncertain automatic answer-to-node matches.

The old `/turns` behavior should remain compatible for ordinary chat input, but the response should support richer message types and node updates.

## Data Model Direction

Avoid a large migration in the first implementation. Use existing tables with explicit JSON metadata first, and treat dedicated columns as a separate schema-hardening follow-up once the behavior is stable.

Project `summary_snapshot` should store `center_context`.

`thinking_nodes` should continue to store tree structure, with detailed node metadata in JSON fields where the current model lacks columns:

- `rationale`
- `expected_answer_type`
- `depth`
- `answer_source`
- `resolved_reason`

`conversation_messages_v2.message_metadata` should support:

- `message_type`
- `linked_node_ids`
- `collapsed_by_default`
- `visible_reasoning_summary`
- `background_questions`
- `question_batch`
- `match_confirmation_id`

Pending answer matches can be represented through `restructure_suggestions` only if that does not confuse structural suggestions. Prefer a small focused model if implementation shows the existing suggestion model is awkward.

## Frontend Behavior

Main workspace:

- Two-column layout.
- Resizable left panel.
- Right map consumes backend nodes as source of truth.
- Remove persistent right inspector column.

Conversation panel:

- Render message types, not just user/assistant bubbles.
- Support collapsible thinking traces.
- Render background batches and question batches.
- Render match confirmation blocks.
- Continue supporting a bottom free-form input.

Mind map:

- Render center and child hierarchy in XMind Clean style.
- Support selected node state.
- Show center popover and ordinary node popover.
- Submit node answers through the node-answer route.
- Fit map to available canvas and handle multiple levels without overlapping text.

## Deterministic Fallback

Fallback must preserve product behavior:

- If center context has very little background, return 3-6 concrete background questions.
- If context has enough background, return 3 concrete thinking questions.
- For node answers, return 1-2 concrete follow-up questions.
- Never fall back to generic "还有什么需要补充？".
- Fallback output must still pass the same schema validators as model output.

## Testing Requirements

Backend tests:

- Initial insufficient context returns 3-6 background questions and no ordinary question nodes.
- Initial sufficient context creates 3-5 first-level question nodes.
- Background answers update center context.
- Node answer marks the node answered and creates 1-3 follow-up child nodes.
- Left-panel batch answer can match multiple open question nodes.
- Medium-confidence matches create a pending confirmation.
- Confirming a match applies answers and creates follow-ups.
- AI invalid output falls back to deterministic stage-appropriate output.
- Auth and ownership behavior remains `401`/`404`.

Frontend tests:

- Workspace renders two columns and no right inspector column.
- Conversation panel renders collapsible thinking trace.
- Conversation panel renders background question batch and question batch.
- Mind map renders center node and multiple first-level question nodes.
- Node popover submits answers.
- Batch answer match confirmation can be accepted.

Manual/browser QA:

- Create a project with sparse background and confirm background-completion flow.
- Create a project with rich background and confirm first-level question nodes.
- Answer one node through popover and confirm child nodes appear.
- Answer multiple nodes from the left panel and confirm match handling.
- Resize the left panel and confirm map remains usable.
