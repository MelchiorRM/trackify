import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import {
  fetchConversations,
  fetchMessages,
  fetchUnreadMessageCount,
  markConversationRead,
  sendMessage,
  startConversation,
} from '@/api/messages'

export function useConversations(params = {}) {
  return useQuery({
    queryKey: ['conversations', params],
    queryFn: () => fetchConversations(params),
    refetchInterval: 30_000,
  })
}

// Polling, not push (see appPlan.txt WHAT THIS PLAN DOES NOT COVER —
// real-time delivery is deferred).
export function useUnreadMessageCount() {
  return useQuery({
    queryKey: ['conversations', 'unread-count'],
    queryFn: fetchUnreadMessageCount,
    refetchInterval: 30_000,
  })
}

export function useMessages(conversationId, params = {}) {
  return useQuery({
    queryKey: ['conversations', conversationId, 'messages', params],
    queryFn: () => fetchMessages(conversationId, params),
    enabled: Boolean(conversationId),
    refetchInterval: 15_000,
  })
}

export function useStartConversation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (username) => startConversation(username),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['conversations'] }),
  })
}

export function useSendMessage(conversationId) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body) => sendMessage(conversationId, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conversations', conversationId, 'messages'] })
      queryClient.invalidateQueries({ queryKey: ['conversations'] })
    },
  })
}

export function useMarkConversationRead(conversationId) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => markConversationRead(conversationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] })
    },
  })
}
