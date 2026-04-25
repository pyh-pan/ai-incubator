export type ThinkingMode = 'diverge' | 'converge' | 'clarify' | 'challenge' | 'validate'
export type ThinkingStage = 'discover' | 'define' | 'develop' | 'deliver'
export type ThinkingNodeKind = 'idea' | 'question' | 'answer' | 'insight' | 'assumption' | 'decision' | 'risk' | 'next_step'
export type ThinkingNodeStatus = 'open' | 'answered' | 'suggested' | 'confirmed'

export interface ConversationMessageV2 {
  id: string
  project_id: string
  node_id: string | null
  role: 'user' | 'assistant'
  source: 'chat' | 'node' | 'system'
  content: string
  thinking_mode: ThinkingMode | null
  stage: ThinkingStage | null
  message_metadata: Record<string, unknown> | null
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

export interface WorkspaceResponse {
  project_id: string
  title: string
  thinking_mode: ThinkingMode | null
  thinking_stage: ThinkingStage | null
  messages: ConversationMessageV2[]
  nodes: ThinkingNode[]
  suggestions: RestructureSuggestion[]
}

export interface TurnRequest {
  content: string
  source: 'chat' | 'node'
  node_id?: string | null
}

export interface TurnResponse extends WorkspaceResponse {
  user_message: ConversationMessageV2
  assistant_message: ConversationMessageV2
}
