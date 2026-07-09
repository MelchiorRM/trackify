import { useState } from 'react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'

export function DiaryEntryForm({ onSubmit, isSubmitting }) {
  const [loggedAt, setLoggedAt] = useState(() => new Date().toISOString().slice(0, 10))
  const [rewatch, setRewatch] = useState(false)
  const [rating, setRating] = useState('')
  const [note, setNote] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    onSubmit({ logged_at: loggedAt, rewatch, rating: rating ? Number(rating) : null, note: note || null })
    setNote('')
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3 rounded-lg border p-4">
      <div className="flex flex-wrap items-end gap-3">
        <div className="space-y-1.5">
          <Label htmlFor="logged_at">Date</Label>
          <Input id="logged_at" type="date" value={loggedAt} onChange={(e) => setLoggedAt(e.target.value)} />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="rating">Rating</Label>
          <Input
            id="rating"
            type="number"
            min="0.5"
            max="5"
            step="0.5"
            value={rating}
            onChange={(e) => setRating(e.target.value)}
            className="w-20"
          />
        </div>
        <label className="flex items-center gap-2 pb-2 text-sm">
          <input type="checkbox" checked={rewatch} onChange={(e) => setRewatch(e.target.checked)} />
          Rewatch
        </label>
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="note">Note</Label>
        <Textarea
          id="note"
          value={note}
          onChange={(e) => setNote(e.target.value)}
          placeholder="Optional note about this session"
        />
      </div>
      <Button type="submit" disabled={isSubmitting} size="sm">
        Log session
      </Button>
    </form>
  )
}
