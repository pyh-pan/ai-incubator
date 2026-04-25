// User types
export interface User {
  id: string
  email: string
  username: string
  created_at: string
  updated_at: string
}

export interface Project {
  id: string
  user_id: string
  title: string
  more_info?: string | null
  framework: string
  status: 'active' | 'archived'
  created_at: string
  updated_at: string
}

// API Response types
export interface ApiResponse<T> {
  data: T
  message?: string
}

export interface ApiError {
  response?: {
    data?: {
      detail?: string
    }
  }
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
