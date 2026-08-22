import { CommentForm } from '@/components/social/CommentForm'
import { CommentList } from '@/components/social/CommentList'
import { LikeButton } from '@/components/social/LikeButton'
import { RepostButton } from '@/components/social/RepostButton'
import { formatDate } from '@/utils/formatters'
import { renderMentions } from '@/utils/mentions'

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
      {review.body && <p className="text-sm leading-relaxed">{renderMentions(review.body)}</p>}
      <div className="flex items-center gap-1 pt-1">
        <LikeButton targetType="review" targetId={review.id} />
        <RepostButton targetType="review" targetId={review.id} />
      </div>
      <div className="space-y-2 border-t pt-2">
        <CommentList targetType="review" targetId={review.id} />
        <CommentForm targetType="review" targetId={review.id} />
      </div>
    </div>
  )
}
