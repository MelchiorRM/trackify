import { useState } from 'react'

import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'

import { StarRating } from './StarRating'

export function ReviewForm({ initialRating, initialBody, onSubmit, isSubmitting }) {
  const [rating, setRating] = useState(initialRating ?? 0)
  const [body, setBody] = useState(initialBody ?? '')
  const [containsSpoiler, setContainsSpoiler] = useState(false)

  const handleSubmit = (e) => {
    e.preventDefault()
    onSubmit({ rating: rating || null, body: body || null, contains_spoiler: containsSpoiler })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <StarRating value={rating} onChange={setRating} />
      <Textarea value={body} onChange={(e) => setBody(e.target.value)} placeholder="Write your review (optional)" />
      <label className="flex items-center gap-2 text-sm text-muted-foreground">
        <input type="checkbox" checked={containsSpoiler} onChange={(e) => setContainsSpoiler(e.target.checked)} />
        Contains spoilers
      </label>
      <Button type="submit" size="sm" disabled={isSubmitting}>
        Save review
      </Button>
    </form>
  )
}
