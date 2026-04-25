import apiClient from './client'
import type { TurnRequest, TurnResponse, WorkspaceResponse } from '../types/incubator'

export const incubatorApi = {
  getWorkspace: async (projectId: string) => {
    const response = await apiClient.get<WorkspaceResponse>(`/v2/projects/${projectId}/workspace`)
    return response.data
  },

  createTurn: async (projectId: string, data: TurnRequest) => {
    const response = await apiClient.post<TurnResponse>(`/v2/projects/${projectId}/turns`, data)
    return response.data
  },
}
