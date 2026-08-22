import { useEffect } from 'react'

import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { useMarkConversationRead, useMessages } from '@/hooks/useMessages'
import { useAuthStore } from '@/store/authStore'
import { formatRelativeTime } from '@/utils/formatters'

import { MessageComposer } from './MessageComposer'

export function MessageThread({ conversationId }) {
  const user = useAuthStore((s) => s.user)
  const { data, isLoading } = useMessages(conversationId)
  const markRead = useMarkConversationRead(conversationId)

  useEffect(() => {
    markRead.mutate()
    // Only re-run when switching threads, not on every poll refetch —
    // deliberately excludes markRead from the dependency list.
  }, [conversationId])

  if (isLoading) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <LoadingSpinner className="h-6 w-6" />
      </div>
    )
  }

  const messages = [...(data?.items ?? [])].reverse()

  return (
    <div className="flex h-full flex-col">
      <div className="flex-1 space-y-2 overflow-y-auto p-3">
        {messages.map((message) => {
          const fromMe = message.sender.id === user?.id
          return (
            <div key={message.id} className={`flex ${fromMe ? 'justify-end' : 'justify-start'}`}>
              <div
                className={`max-w-[75%] rounded-lg px-3 py-1.5 text-sm ${
                  fromMe ? 'bg-primary text-primary-foreground' : 'bg-muted'
                }`}
              >
                <p>{message.body}</p>
                <p className={`mt-0.5 text-[10px] ${fromMe ? 'text-primary-foreground/70' : 'text-muted-foreground'}`}>
                  {formatRelativeTime(message.created_at)}
                </p>
              </div>
            </div>
          )
        })}
      </div>
      <MessageComposer conversationId={conversationId} />
    </div>
  )
}
