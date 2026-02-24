import apiClient from './client'
import type {
  User,
  Project,
  MindmapNode,
  LoginRequest,
  RegisterRequest,
  AuthResponse,
  FrameworkRecommendation,
  QuestionGeneration,
  ExtractedPoints,
  FrameworkType,
} from '../types'

// Auth APIs
export const authApi = {
  login: async (data: LoginRequest) => {
    const response = await apiClient.post<AuthResponse>('/auth/login', data)
    return response.data
  },

  register: async (data: RegisterRequest) => {
    const response = await apiClient.post<AuthResponse>('/auth/register', data)
    return response.data
  },

  getCurrentUser: async () => {
    const response = await apiClient.get<User>('/auth/me')
    return response.data
  },
}

// Project APIs
export const projectApi = {
  create: async (data: { title: string; framework: FrameworkType }) => {
    const response = await apiClient.post<Project>('/projects', data)
    return response.data
  },

  list: async () => {
    const response = await apiClient.get<Project[]>('/projects')
    return response.data
  },

  getById: async (id: string) => {
    const response = await apiClient.get<Project>(`/projects/${id}`)
    return response.data
  },

  update: async (id: string, data: Partial<Project>) => {
    const response = await apiClient.put<Project>(`/projects/${id}`, data)
    return response.data
  },

  delete: async (id: string) => {
    await apiClient.delete(`/projects/${id}`)
  },
}

// Node APIs
export const nodeApi = {
  create: async (data: Partial<MindmapNode>) => {
    const response = await apiClient.post<MindmapNode>('/nodes', data)
    return response.data
  },

  update: async (id: string, data: Partial<MindmapNode>) => {
    const response = await apiClient.put<MindmapNode>(`/nodes/${id}`, data)
    return response.data
  },

  delete: async (id: string) => {
    await apiClient.delete(`/nodes/${id}`)
  },

  getChildren: async (id: string) => {
    const response = await apiClient.get<MindmapNode[]>(`/nodes/${id}/children`)
    return response.data
  },

  getByProject: async (projectId: string) => {
    const response = await apiClient.get<MindmapNode[]>(`/projects/${projectId}/mindmap`)
    return response.data
  },
}

// AI APIs
export const aiApi = {
  recommendFramework: async (idea: string) => {
    const response = await apiClient.post<FrameworkRecommendation>('/ai/recommend-framework', { idea })
    return response.data
  },

  generateQuestion: async (framework: FrameworkType, context: string) => {
    const response = await apiClient.post<QuestionGeneration>('/ai/generate-question', {
      framework,
      context,
    })
    return response.data
  },

  extractPoints: async (answer: string) => {
    const response = await apiClient.post<ExtractedPoints>('/ai/extract-points', {
      answer,
    })
    return response.data
  },

  generateFollowUp: async (nodeId: string, parentAnswer: string) => {
    const response = await apiClient.post<QuestionGeneration>(`/ai/followup/${nodeId}`, {
      parent_answer: parentAnswer,
    })
    return response.data
  },
}
