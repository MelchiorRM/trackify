import { Heart } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { useCreateLike, useDeleteLike, useLikes } from '@/hooks/useLikes'
import { useAuthStore } from '@/store/authStore'

export function LikeButton({ targetType, targetId }) {
  const user = useAuthStore((s) => s.user)
  const { data: likes } = useLikes(targetType, targetId)
  const createLike = useCreateLike(targetType, targetId)
  const deleteLike = useDeleteLike(targetType, targetId)

  const items = likes?.items ?? []
  const likedByMe = items.some((like) => like.user.id === user?.id)
  const isPending = createLike.isPending || deleteLike.isPending

  const handleClick = () => {
    if (likedByMe) {
      deleteLike.mutate()
    } else {
      createLike.mutate()
    }
  }

  return (
    <Button
      size="sm"
      variant="ghost"
      disabled={isPending}
      onClick={handleClick}
      className="gap-1.5"
      aria-label={likedByMe ? 'Unlike' : 'Like'}
    >
      <Heart className={`h-4 w-4 ${likedByMe ? 'fill-destructive text-destructive' : ''}`} />
      {items.length > 0 && <span className="text-xs text-muted-foreground">{items.length}</span>}
    </Button>
  )
}
