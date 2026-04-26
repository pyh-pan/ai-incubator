import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { message } from 'antd'
import { incubatorApi } from '../api/incubator'
import type { ApiError } from '../types'
import type { TurnRequest, WorkspaceResponse } from '../types/incubator'

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

  const nodeAnswerMutation = useMutation({
    mutationFn: ({ nodeId, content }: { nodeId: string; content: string }) =>
      incubatorApi.answerNode(projectId!, nodeId, { content }),
    onSuccess: (data) => {
      queryClient.setQueryData<WorkspaceResponse>(['v2-workspace', projectId], data)
    },
    onError: (error: ApiError) => {
      message.error(error.response?.data?.detail || '回答节点失败，请重试')
    },
  })

  return {
    workspace: workspaceQuery.data,
    isLoading: workspaceQuery.isLoading,
    isThinking: turnMutation.isPending || suggestionMutation.isPending || nodeAnswerMutation.isPending,
    submitTurn: turnMutation.mutate,
    answerNode: (nodeId: string, content: string) => nodeAnswerMutation.mutate({ nodeId, content }),
    acceptSuggestion: (id: string) => suggestionMutation.mutate({ id, action: 'accept' }),
    rejectSuggestion: (id: string) => suggestionMutation.mutate({ id, action: 'reject' }),
  }
}
