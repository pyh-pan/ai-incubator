import apiClient from './client'
import type { NodeAnswerRequest, TurnRequest, TurnResponse, WorkspaceResponse } from '../types/incubator'

export const incubatorApi = {
  getWorkspace: async (projectId: string) => {
    const response = await apiClient.get<WorkspaceResponse>(`/v2/projects/${projectId}/workspace`)
    return response.data
  },

  createTurn: async (projectId: string, data: TurnRequest) => {
    const response = await apiClient.post<TurnResponse>(`/v2/projects/${projectId}/turns`, data)
    return response.data
  },

  answerNode: async (projectId: string, nodeId: string, data: NodeAnswerRequest) => {
    const response = await apiClient.post<WorkspaceResponse>(`/v2/projects/${projectId}/nodes/${nodeId}/answer`, data)
    return response.data
  },

  acceptSuggestion: async (suggestionId: string) => {
    const response = await apiClient.post<WorkspaceResponse>(`/v2/restructure-suggestions/${suggestionId}/accept`)
    return response.data
  },

  rejectSuggestion: async (suggestionId: string) => {
    const response = await apiClient.post<WorkspaceResponse>(`/v2/restructure-suggestions/${suggestionId}/reject`)
    return response.data
  },
}
