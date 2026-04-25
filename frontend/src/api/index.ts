import apiClient from './client'
export { incubatorApi } from './incubator'

import type {
  User,
  Project,
  LoginRequest,
  RegisterRequest,
  AuthResponse,
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
  create: async (data: { title: string; more_info?: string }) => {
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
