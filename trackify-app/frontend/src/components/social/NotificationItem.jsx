import { Link } from 'react-router-dom'

import { formatRelativeTime } from '@/utils/formatters'

const VERBS = {
  follow: 'followed you',
  like: 'liked your',
  comment: 'commented on your',
  mention: 'mentioned you in a',
  repost: 'reposted your',
}

function targetLabel(notification) {
  if (notification.type === 'follow') return null
  return notification.target_type ?? 'post'
}

export function NotificationItem({ notification, onClick }) {
  const verb = VERBS[notification.type] ?? notification.type
  const target = targetLabel(notification)

  return (
    <div
      className={`flex items-start gap-2 rounded-md p-2 text-sm ${notification.read ? '' : 'bg-accent/50'}`}
      onClick={onClick}
    >
      <div className="flex-1">
        <Link to={`/profile/${notification.actor.username}`} className="font-medium hover:underline">
          {notification.actor.username}
        </Link>{' '}
        <span className="text-muted-foreground">
          {verb} {target}
        </span>
      </div>
      <span className="whitespace-nowrap text-xs text-muted-foreground">
        {formatRelativeTime(notification.created_at)}
      </span>
    </div>
  )
}
