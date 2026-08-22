import { Link } from 'react-router-dom'

import { EmptyState } from '@/components/common/EmptyState'
import { useConversations } from '@/hooks/useMessages'
import { formatRelativeTime } from '@/utils/formatters'

export function ConversationList({ activeConversationId }) {
  const { data } = useConversations()
  const conversations = data?.items ?? []

  if (conversations.length === 0) {
    return <EmptyState title="No conversations yet" description="Message someone from their profile." />
  }

  return (
    <ul className="divide-y">
      {conversations.map((conversation) => (
        <li key={conversation.id}>
          <Link
            to={`/messages/${conversation.id}`}
            className={`flex items-center justify-between gap-2 p-3 hover:bg-accent ${
              conversation.id === activeConversationId ? 'bg-accent' : ''
            }`}
          >
            <div className="min-w-0">
              <p className="font-medium">{conversation.other_user.username}</p>
              <p className="truncate text-sm text-muted-foreground">
                {conversation.last_message?.body ?? 'No messages yet'}
              </p>
            </div>
            <div className="flex flex-shrink-0 flex-col items-end gap-1">
              {conversation.last_message && (
                <span className="text-xs text-muted-foreground">
                  {formatRelativeTime(conversation.last_message.created_at)}
                </span>
              )}
              {conversation.unread_count > 0 && (
                <span className="flex h-4 min-w-4 items-center justify-center rounded-full bg-primary px-1 text-[10px] font-medium text-primary-foreground">
                  {conversation.unread_count}
                </span>
              )}
            </div>
          </Link>
        </li>
      ))}
    </ul>
  )
}
