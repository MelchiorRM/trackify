import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { EmptyState } from '@/components/common/EmptyState'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { StatusBadge } from '@/components/library/StatusBadge'
import { DomainBadge } from '@/components/media/DomainBadge'
import { MediaGrid } from '@/components/media/MediaGrid'
import { PostCard } from '@/components/posts/PostCard'
import { FavoritesPicker } from '@/components/profile/FavoritesPicker'
import { FavoritesRow } from '@/components/profile/FavoritesRow'
import { FollowButton } from '@/components/social/FollowButton'
import { Button } from '@/components/ui/button'
import { useStartConversation } from '@/hooks/useMessages'
import { useUserPosts } from '@/hooks/usePosts'
import { useProfile, useProfileLibrary, useProfileReviews } from '@/hooks/useProfile'
import { useAuthStore } from '@/store/authStore'
import { formatDate } from '@/utils/formatters'

export default function Profile() {
  const { username } = useParams()
  const navigate = useNavigate()
  const currentUser = useAuthStore((s) => s.user)
  const isOwnProfile = currentUser?.username === username
  const [view, setView] = useState('grid')
  const [editingFavorites, setEditingFavorites] = useState(false)

  const { data: profile, isLoading: profileLoading } = useProfile(username)
  const { data: library, isLoading: libraryLoading } = useProfileLibrary(username)
  const { data: reviews } = useProfileReviews(username)
  const { data: posts } = useUserPosts(username)
  const startConversation = useStartConversation()

  const handleMessage = () => {
    startConversation.mutate(username, {
      onSuccess: (conversation) => navigate(`/messages/${conversation.id}`),
    })
  }

  if (profileLoading || !profile) {
    return (
      <div className="flex justify-center py-16">
        <LoadingSpinner className="h-8 w-8" />
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6 px-4 py-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">{profile.username}</h1>
          {/* Public stats summary — derived from the already-public
              library/reviews lists rather than the private /stats/me
              endpoint, which only ever answers for the caller themselves. */}
          <p className="text-sm text-muted-foreground">
            Joined {formatDate(profile.created_at)} · {library?.length ?? 0} tracked · {reviews?.length ?? 0} reviews
          </p>
        </div>
        {isOwnProfile && (
          <div className="flex gap-2">
            <Button size="sm" variant="outline" asChild>
              <Link to="/settings">Edit profile</Link>
            </Button>
            <Button size="sm" onClick={() => setEditingFavorites((v) => !v)}>
              {editingFavorites ? 'Close' : 'Edit favorites'}
            </Button>
          </div>
        )}
        {!isOwnProfile && currentUser && (
          <div className="flex gap-2">
            <FollowButton username={username} />
            <Button size="sm" variant="outline" disabled={startConversation.isPending} onClick={handleMessage}>
              Message
            </Button>
          </div>
        )}
      </div>

      {editingFavorites ? (
        <FavoritesPicker
          initialItemIds={profile.favorites.map((f) => f.item.id)}
          onDone={() => setEditingFavorites(false)}
        />
      ) : (
        <FavoritesRow favorites={profile.favorites} />
      )}

      <section>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-lg font-semibold">Library</h2>
          <div className="flex gap-2 text-sm">
            <button
              type="button"
              onClick={() => setView('grid')}
              className={view === 'grid' ? 'font-medium underline' : 'text-muted-foreground'}
            >
              Grid
            </button>
            <span className="text-muted-foreground">/</span>
            <button
              type="button"
              onClick={() => setView('list')}
              className={view === 'list' ? 'font-medium underline' : 'text-muted-foreground'}
            >
              List
            </button>
          </div>
        </div>

        {libraryLoading && <LoadingSpinner className="mx-auto h-8 w-8" />}
        {!libraryLoading && library?.length === 0 && <EmptyState title="Nothing tracked yet" />}
        {!libraryLoading && library?.length > 0 && view === 'grid' && (
          <MediaGrid items={library.map((entry) => entry.item)} />
        )}
        {!libraryLoading && library?.length > 0 && view === 'list' && (
          <div className="space-y-2">
            {library.map((entry) => (
              <div key={entry.id} className="flex items-center gap-3 rounded-lg border p-3">
                <DomainBadge domain={entry.item.domain} />
                <Link
                  to={`/item/${entry.item.domain}/${entry.item.external_id}`}
                  className="flex-1 truncate font-medium hover:underline"
                >
                  {entry.item.title}
                </Link>
                <StatusBadge status={entry.status} />
              </div>
            ))}
          </div>
        )}
      </section>

      <section>
        <h2 className="mb-3 text-lg font-semibold">Posts</h2>
        {(posts?.items?.length ?? 0) === 0 ? (
          <EmptyState title="No posts yet" />
        ) : (
          <div className="space-y-3">
            {posts.items.map((post) => (
              <PostCard key={post.id} post={post} />
            ))}
          </div>
        )}
      </section>
    </div>
  )
}
