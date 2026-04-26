export type ThinkingMode = 'diverge' | 'converge' | 'clarify' | 'challenge' | 'validate'
export type ThinkingStage = 'discover' | 'define' | 'develop' | 'deliver'
export type ThinkingNodeKind = 'idea' | 'question' | 'answer' | 'insight' | 'assumption' | 'decision' | 'risk' | 'next_step' | 'followup'
export type ThinkingNodeStatus = 'open' | 'answered' | 'suggested' | 'confirmed' | 'needs_context' | 'resolved'
export type MessageType =
  | 'background_question_batch'
  | 'question_batch'
  | 'user_answer'
  | 'batch_answer'
  | 'batch_answer_candidate'
  | 'match_confirmation'
  | 'assistant_followup'
  | 'chat_background'

export interface CenterContext {
  original_idea: string
  idea_summary: string | null
  background_summary: string | null
  known_facts: string[]
  assumptions: string[]
  constraints: string[]
  target_users: string[]
  desired_outcomes: string[]
  unresolved_context_gaps: string[]
  context_sufficiency: 'unknown' | 'insufficient' | 'sufficient'
}

export interface QuestionBatchItem {
  question: string
  short_title?: string
  why_this_matters?: string
  why_needed?: string
  expected_answer_type?: string
  expected_signal?: string
}

export interface AnswerMatch {
  node_id: string
  extracted_answer: string
  confidence: 'high' | 'medium' | 'low'
}

export interface ConversationMetadata {
  message_type?: MessageType
  linked_node_ids?: string[]
  collapsed_by_default?: boolean
  visible_reasoning_summary?: string
  background_questions?: QuestionBatchItem[]
  question_batch?: QuestionBatchItem[]
  follow_up_questions?: QuestionBatchItem[]
  answer_matches?: AnswerMatch[]
}

export interface ConversationMessageV2 {
  id: string
  project_id: string
  node_id: string | null
  role: 'user' | 'assistant'
  source: 'chat' | 'node' | 'system'
  content: string
  thinking_mode: ThinkingMode | null
  stage: ThinkingStage | null
  message_metadata: ConversationMetadata | null
  created_at: string
}

export interface ThinkingNode {
  id: string
  project_id: string
  parent_id: string | null
  kind: ThinkingNodeKind
  status: ThinkingNodeStatus
  title: string
  summary: string | null
  question: string | null
  answer_summary: string | null
  sort_order: number
  layout: Record<string, unknown> | null
  source_message_ids: string[]
  confidence: number
  created_at: string
  updated_at: string
}

export interface MapOperation {
  type: 'create_node' | 'update_node' | 'mark_answered' | 'move_node' | 'rename_node' | 'merge_nodes' | 'split_node' | 'delete_node'
  node_id?: string | null
  parent_id?: string | null
  title?: string | null
  kind?: ThinkingNodeKind | null
  status?: ThinkingNodeStatus | null
  summary?: string | null
  question?: string | null
  source_node_ids?: string[]
}

export interface RestructureSuggestion {
  id: string
  project_id: string
  status: 'pending' | 'accepted' | 'rejected'
  operations: MapOperation[]
  rationale: string
  created_from_message_id: string | null
  created_at: string
  resolved_at: string | null
}

export interface AnswerMatchResponse {
  id: string
  project_id: string
  status: string
  matches: AnswerMatch[]
  original_content: string
  confidence: 'high' | 'medium' | 'low'
  created_at: string
}

export interface WorkspaceResponse {
  project_id: string
  title: string
  thinking_mode: ThinkingMode | null
  thinking_stage: ThinkingStage | null
  center_context: CenterContext
  messages: ConversationMessageV2[]
  nodes: ThinkingNode[]
  suggestions: RestructureSuggestion[]
  answer_matches: AnswerMatchResponse[]
}

export interface TurnRequest {
  content: string
  source: 'chat' | 'node'
  node_id?: string | null
}

export interface NodeAnswerRequest {
  content: string
}

export interface TurnResponse extends WorkspaceResponse {
  user_message: ConversationMessageV2
  assistant_message: ConversationMessageV2
}
