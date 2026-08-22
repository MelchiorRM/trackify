import { useParams } from 'react-router-dom'

import { EmptyState } from '@/components/common/EmptyState'
import { ConversationList } from '@/components/messages/ConversationList'
import { MessageThread } from '@/components/messages/MessageThread'

export default function Messages() {
  const { conversationId } = useParams()

  return (
    <div className="mx-auto grid h-[calc(100vh-4rem)] max-w-4xl grid-cols-1 border-x sm:grid-cols-[280px_1fr]">
      <div className="hidden overflow-y-auto border-r sm:block">
        <ConversationList activeConversationId={conversationId} />
      </div>
      {conversationId ? (
        <MessageThread conversationId={conversationId} />
      ) : (
        <div className="hidden items-center justify-center sm:flex">
          <EmptyState title="Select a conversation" description="Pick a conversation from the list." />
        </div>
      )}
      {!conversationId && (
        <div className="overflow-y-auto sm:hidden">
          <ConversationList activeConversationId={conversationId} />
        </div>
      )}
    </div>
  )
}
