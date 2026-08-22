import { useState } from 'react'

import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { useCreateComment } from '@/hooks/useComments'

export function CommentForm({ targetType, targetId }) {
  const [body, setBody] = useState('')
  const createComment = useCreateComment(targetType, targetId)

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!body.trim()) return
    createComment.mutate(body, { onSuccess: () => setBody('') })
  }

  return (
    <form onSubmit={handleSubmit} className="flex items-start gap-2">
      <Textarea
        value={body}
        onChange={(e) => setBody(e.target.value)}
        placeholder="Write a comment..."
        className="h-9 min-h-0"
      />
      <Button type="submit" size="sm" disabled={createComment.isPending || !body.trim()}>
        Post
      </Button>
    </form>
  )
}
