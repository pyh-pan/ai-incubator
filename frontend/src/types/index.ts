// User types
export interface User {
  id: string
  email: string
  username: string
  created_at: string
  updated_at: string
}

// Project types
export type FrameworkType = 'product_manager' | 'business_canvas' | 'technical_feasibility' | 'socratic' | 'general'

export interface Project {
  id: string
  user_id: string
  title: string
  framework: FrameworkType
  status: 'active' | 'archived'
  created_at: string
  updated_at: string
}

// Node types
export type NodeStatus = 'unanswered' | 'in_progress' | 'answered'

export interface MindmapNode {
  id: string
  project_id: string
  parent_id: string | null
  label: string
  question: string
  context: string
  answer: string | null
  extracted_points: string[] | null
  status: NodeStatus
  depth: number
  position: { x: number; y: number } | null
  created_at: string
  updated_at: string
  children?: MindmapNode[]
}

// AI types
export interface FrameworkRecommendation {
  framework: FrameworkType
  confidence: number
  reason: string
}

export interface QuestionGeneration {
  question: string
  context: string
  examples: string[]
}

export interface ExtractedPoints {
  points: string[]
  summary: string
}

// API Response types
export interface ApiResponse<T> {
  data: T
  message?: string
}

export interface ApiError {
  detail: string
  status_code: number
}

// Auth types
export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  username: string
  password: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user: User
}
