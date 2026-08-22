import { useState } from 'react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useSendMessage } from '@/hooks/useMessages'

export function MessageComposer({ conversationId }) {
  const [body, setBody] = useState('')
  const sendMessage = useSendMessage(conversationId)

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!body.trim()) return
    sendMessage.mutate(body, { onSuccess: () => setBody('') })
  }

  return (
    <form onSubmit={handleSubmit} className="flex items-center gap-2 border-t p-3">
      <Input
        value={body}
        onChange={(e) => setBody(e.target.value)}
        placeholder="Write a message..."
        maxLength={2000}
      />
      <Button type="submit" size="sm" disabled={sendMessage.isPending || !body.trim()}>
        Send
      </Button>
    </form>
  )
}
