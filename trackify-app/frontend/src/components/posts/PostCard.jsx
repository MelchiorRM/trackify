import { CommentForm } from '@/components/social/CommentForm'
import { CommentList } from '@/components/social/CommentList'
import { LikeButton } from '@/components/social/LikeButton'
import { RepostButton } from '@/components/social/RepostButton'
import { formatDate } from '@/utils/formatters'
import { renderMentions } from '@/utils/mentions'

export function PostCard({ post }) {
  return (
    <div className="space-y-2 rounded-lg border p-4">
      <div className="flex items-center justify-between">
        <span className="text-xs text-muted-foreground">{formatDate(post.created_at)}</span>
      </div>
      <p className="text-sm leading-relaxed">{renderMentions(post.body)}</p>
      <div className="flex items-center gap-1 pt-1">
        <LikeButton targetType="post" targetId={post.id} />
        <RepostButton targetType="post" targetId={post.id} />
      </div>
      <div className="space-y-2 border-t pt-2">
        <CommentList targetType="post" targetId={post.id} />
        <CommentForm targetType="post" targetId={post.id} />
      </div>
    </div>
  )
}
