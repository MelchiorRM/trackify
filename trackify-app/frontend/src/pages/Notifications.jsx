import { EmptyState } from '@/components/common/EmptyState'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { NotificationItem } from '@/components/social/NotificationItem'
import { Button } from '@/components/ui/button'
import {
  useMarkAllNotificationsRead,
  useMarkNotificationRead,
  useNotifications,
} from '@/hooks/useNotifications'

export default function Notifications() {
  const { data, isLoading } = useNotifications({ limit: 50 })
  const markRead = useMarkNotificationRead()
  const markAllRead = useMarkAllNotificationsRead()

  const notifications = data?.items ?? []

  return (
    <div className="mx-auto max-w-2xl space-y-4 px-4 py-8">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold tracking-tight">Notifications</h1>
        <Button size="sm" variant="outline" onClick={() => markAllRead.mutate()} disabled={markAllRead.isPending}>
          Mark all read
        </Button>
      </div>

      {isLoading && (
        <div className="flex justify-center py-8">
          <LoadingSpinner className="h-6 w-6" />
        </div>
      )}

      {!isLoading && notifications.length === 0 && (
        <EmptyState title="No notifications yet" description="Likes, comments, and follows will show up here." />
      )}

      {!isLoading && notifications.length > 0 && (
        <div className="space-y-1 rounded-lg border p-2">
          {notifications.map((notification) => (
            <NotificationItem
              key={notification.id}
              notification={notification}
              onClick={() => !notification.read && markRead.mutate(notification.id)}
            />
          ))}
        </div>
      )}
    </div>
  )
}
