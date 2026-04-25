import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { message } from 'antd'
import { incubatorApi } from '../api/incubator'
import type { TurnRequest, WorkspaceResponse } from '../types/incubator'

interface ApiError {
  response?: {
    data?: {
      detail?: string
    }
  }
}

export function useIncubatorSession(projectId: string | undefined) {
  const queryClient = useQueryClient()

  const workspaceQuery = useQuery({
    queryKey: ['v2-workspace', projectId],
    queryFn: () => incubatorApi.getWorkspace(projectId!),
    enabled: Boolean(projectId),
  })

  const turnMutation = useMutation({
    mutationFn: (request: TurnRequest) => incubatorApi.createTurn(projectId!, request),
    onSuccess: (data) => {
      queryClient.setQueryData<WorkspaceResponse>(['v2-workspace', projectId], data)
    },
    onError: (error: ApiError) => {
      message.error(error.response?.data?.detail || 'AI 思考失败，请重试')
    },
  })

  const suggestionMutation = useMutation({
    mutationFn: ({ id, action }: { id: string; action: 'accept' | 'reject' }) =>
      action === 'accept' ? incubatorApi.acceptSuggestion(id) : incubatorApi.rejectSuggestion(id),
    onSuccess: (data) => {
      queryClient.setQueryData<WorkspaceResponse>(['v2-workspace', projectId], data)
    },
    onError: (error: ApiError) => {
      message.error(error.response?.data?.detail || '处理建议失败，请重试')
    },
  })

  return {
    workspace: workspaceQuery.data,
    isLoading: workspaceQuery.isLoading,
    isThinking: turnMutation.isPending || suggestionMutation.isPending,
    submitTurn: turnMutation.mutate,
    acceptSuggestion: (id: string) => suggestionMutation.mutate({ id, action: 'accept' }),
    rejectSuggestion: (id: string) => suggestionMutation.mutate({ id, action: 'reject' }),
  }
}
