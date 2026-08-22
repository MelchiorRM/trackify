import { Link } from 'react-router-dom'

import { EmptyState } from '@/components/common/EmptyState'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { DomainBadge } from '@/components/media/DomainBadge'
import { useFeed } from '@/hooks/useSocial'
import { formatRelativeTime } from '@/utils/formatters'
import { renderMentions } from '@/utils/mentions'

import { LikeButton } from './LikeButton'
import { RepostButton } from './RepostButton'

function FeedActor({ actor }) {
  return (
    <Link to={`/profile/${actor.username}`} className="font-medium hover:underline">
      {actor.username}
    </Link>
  )
}

function FeedLine({ createdAt, children }) {
  return (
    <div className="flex items-start justify-between gap-2 rounded-lg border p-3 text-sm">
      <div>{children}</div>
      <span className="whitespace-nowrap text-xs text-muted-foreground">{formatRelativeTime(createdAt)}</span>
    </div>
  )
}

function FeedItemRow({ item }) {
  const { type, actor, created_at: createdAt, data } = item

  switch (type) {
    case 'post':
      return (
        <div className="space-y-2 rounded-lg border p-4">
          <div className="flex items-center justify-between">
            <FeedActor actor={actor} />
            <span className="text-xs text-muted-foreground">{formatRelativeTime(createdAt)}</span>
          </div>
          <p className="text-sm leading-relaxed">{renderMentions(data.body)}</p>
          <div className="flex items-center gap-1 pt-1">
            <LikeButton targetType="post" targetId={data.post_id} />
            <RepostButton targetType="post" targetId={data.post_id} />
          </div>
        </div>
      )

    case 'library':
      return (
        <FeedLine createdAt={createdAt}>
          <FeedActor actor={actor} /> {data.status === 'completed' ? 'completed' : 'added'}{' '}
          <Link to={`/item/${data.item_domain}/${data.item_external_id}`} className="hover:underline">
            {data.item_title}
          </Link>
          <DomainBadge domain={data.item_domain} className="ml-2" />
        </FeedLine>
      )

    case 'review':
      return (
        <FeedLine createdAt={createdAt}>
          <FeedActor actor={actor} /> reviewed{' '}
          <Link to={`/item/${data.item_domain}/${data.item_external_id}`} className="hover:underline">
            {data.item_title}
          </Link>
          {data.rating != null && <span className="text-muted-foreground"> · ★ {data.rating}</span>}
          {data.body && <p className="mt-1 text-muted-foreground">{renderMentions(data.body)}</p>}
        </FeedLine>
      )

    case 'collection':
      return (
        <FeedLine createdAt={createdAt}>
          <FeedActor actor={actor} /> created a list{' '}
          <Link to={`/collections/${data.collection_id}`} className="hover:underline">
            {data.name}
          </Link>{' '}
          <span className="text-muted-foreground">({data.item_count} items)</span>
        </FeedLine>
      )

    case 'follow':
      return (
        <FeedLine createdAt={createdAt}>
          <FeedActor actor={actor} /> followed{' '}
          <Link to={`/profile/${data.followed_username}`} className="hover:underline">
            {data.followed_username}
          </Link>
        </FeedLine>
      )

    case 'like':
      return (
        <FeedLine createdAt={createdAt}>
          <FeedActor actor={actor} /> liked a {data.target_type}
        </FeedLine>
      )

    case 'comment':
      return (
        <FeedLine createdAt={createdAt}>
          <FeedActor actor={actor} /> commented on a {data.target_type}
          <p className="mt-1 text-muted-foreground">{renderMentions(data.body)}</p>
        </FeedLine>
      )

    case 'repost':
      return (
        <FeedLine createdAt={createdAt}>
          <FeedActor actor={actor} /> reposted a {data.target_type}
          {data.comment && <p className="mt-1">{renderMentions(data.comment)}</p>}
        </FeedLine>
      )

    default:
      return null
  }
}

export function ActivityFeed() {
  const { data, isLoading } = useFeed({ limit: 20 })

  if (isLoading) {
    return (
      <div className="flex justify-center py-8">
        <LoadingSpinner className="h-6 w-6" />
      </div>
    )
  }

  const items = data?.items ?? []
  if (items.length === 0) {
    return <EmptyState title="Your feed is empty" description="Follow other users to see their activity here." />
  }

  return (
    <div className="space-y-3">
      {items.map((item) => (
        <FeedItemRow key={item.id} item={item} />
      ))}
    </div>
  )
}
