import { useState } from 'react'

import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { useCreatePost } from '@/hooks/usePosts'

const MAX_LENGTH = 500

export function PostComposer() {
  const [body, setBody] = useState('')
  const createPost = useCreatePost()

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!body.trim()) return
    createPost.mutate(body, { onSuccess: () => setBody('') })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-2 rounded-lg border p-4">
      <Textarea
        value={body}
        onChange={(e) => setBody(e.target.value)}
        placeholder="Share something with your followers..."
        maxLength={MAX_LENGTH}
      />
      <div className="flex items-center justify-between">
        <span className="text-xs text-muted-foreground">
          {body.length}/{MAX_LENGTH}
        </span>
        <Button type="submit" size="sm" disabled={createPost.isPending || !body.trim()}>
          Post
        </Button>
      </div>
    </form>
  )
}
