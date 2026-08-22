import { Repeat2 } from 'lucide-react'
import { useState } from 'react'

import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { useCreateRepost } from '@/hooks/useReposts'

export function RepostButton({ targetType, targetId }) {
  const [open, setOpen] = useState(false)
  const [comment, setComment] = useState('')
  const createRepost = useCreateRepost(targetType, targetId)
  const done = createRepost.isSuccess

  const handleRepost = () => {
    createRepost.mutate(comment || null, {
      onSuccess: () => setOpen(false),
    })
  }

  if (!open) {
    return (
      <Button size="sm" variant="ghost" className="gap-1.5" onClick={() => setOpen(true)} disabled={done}>
        <Repeat2 className={`h-4 w-4 ${done ? 'text-primary' : ''}`} />
        {done ? 'Reposted' : 'Repost'}
      </Button>
    )
  }

  return (
    <div className="flex items-center gap-2">
      <Textarea
        value={comment}
        onChange={(e) => setComment(e.target.value)}
        placeholder="Add a quote (optional)"
        className="h-9 min-h-0"
      />
      <Button size="sm" disabled={createRepost.isPending} onClick={handleRepost}>
        Repost
      </Button>
      <Button size="sm" variant="ghost" onClick={() => setOpen(false)}>
        Cancel
      </Button>
    </div>
  )
}
