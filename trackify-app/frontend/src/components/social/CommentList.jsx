import { Link } from 'react-router-dom'

import { useComments, useDeleteComment } from '@/hooks/useComments'
import { useAuthStore } from '@/store/authStore'
import { formatRelativeTime } from '@/utils/formatters'
import { renderMentions } from '@/utils/mentions'

export function CommentList({ targetType, targetId }) {
  const user = useAuthStore((s) => s.user)
  const { data } = useComments(targetType, targetId)
  const deleteComment = useDeleteComment(targetType, targetId)

  const comments = data?.items ?? []
  if (comments.length === 0) {
    return <p className="text-sm text-muted-foreground">No comments yet.</p>
  }

  return (
    <ul className="space-y-3">
      {comments.map((comment) => (
        <li key={comment.id} className="text-sm">
          <div className="flex items-center justify-between">
            <Link to={`/profile/${comment.user.username}`} className="font-medium hover:underline">
              {comment.user.username}
            </Link>
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <span>{formatRelativeTime(comment.created_at)}</span>
              {comment.user.id === user?.id && (
                <button
                  type="button"
                  onClick={() => deleteComment.mutate(comment.id)}
                  className="hover:text-destructive"
                >
                  Delete
                </button>
              )}
            </div>
          </div>
          <p className="mt-0.5">{renderMentions(comment.body)}</p>
        </li>
      ))}
    </ul>
  )
}
