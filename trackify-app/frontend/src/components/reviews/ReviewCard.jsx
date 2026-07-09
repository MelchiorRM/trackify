import { formatDate } from '@/utils/formatters'

import { StarRating } from './StarRating'

export function ReviewCard({ review }) {
  return (
    <div className="space-y-2 rounded-lg border p-4">
      <div className="flex items-center justify-between">
        {review.rating != null && <StarRating value={review.rating} readOnly size={16} />}
        <span className="text-xs text-muted-foreground">{formatDate(review.created_at)}</span>
      </div>
      {review.contains_spoiler && (
        <p className="text-xs font-medium uppercase tracking-wide text-destructive">Contains spoilers</p>
      )}
      {review.body && <p className="text-sm leading-relaxed">{review.body}</p>}
    </div>
  )
}
