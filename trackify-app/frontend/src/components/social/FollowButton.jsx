import { Button } from '@/components/ui/button'
import { useFollow, useFollowing, useUnfollow } from '@/hooks/useSocial'

export function FollowButton({ username }) {
  const { data: following } = useFollowing()
  const follow = useFollow()
  const unfollow = useUnfollow()

  const isFollowing = following?.items.some((f) => f.user.username === username) ?? false
  const isPending = follow.isPending || unfollow.isPending

  const handleClick = () => {
    if (isFollowing) {
      unfollow.mutate(username)
    } else {
      follow.mutate(username)
    }
  }

  return (
    <Button size="sm" variant={isFollowing ? 'outline' : 'default'} disabled={isPending} onClick={handleClick}>
      {isFollowing ? 'Following' : 'Follow'}
    </Button>
  )
}
