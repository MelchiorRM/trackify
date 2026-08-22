import { Bell } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import { useMarkNotificationRead, useNotifications, useUnreadNotificationCount } from '@/hooks/useNotifications'

import { NotificationItem } from './NotificationItem'

export function NotificationBell() {
  const [open, setOpen] = useState(false)
  const { data: unread } = useUnreadNotificationCount()
  const { data } = useNotifications({ limit: 5 })
  const markRead = useMarkNotificationRead()

  const count = unread?.count ?? 0
  const notifications = data?.items ?? []

  return (
    <div className="relative">
      <Button
        variant="ghost"
        size="icon"
        className="relative"
        aria-label="Notifications"
        onClick={() => setOpen((v) => !v)}
      >
        <Bell className="h-5 w-5" />
        {count > 0 && (
          <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-destructive px-1 text-[10px] font-medium text-destructive-foreground">
            {count > 9 ? '9+' : count}
          </span>
        )}
      </Button>

      {open && (
        <div className="absolute right-0 z-50 mt-2 w-80 rounded-lg border bg-popover p-2 text-popover-foreground shadow-md">
          {notifications.length === 0 ? (
            <p className="p-2 text-sm text-muted-foreground">No notifications yet.</p>
          ) : (
            <div className="space-y-1">
              {notifications.map((notification) => (
                <NotificationItem
                  key={notification.id}
                  notification={notification}
                  onClick={() => !notification.read && markRead.mutate(notification.id)}
                />
              ))}
            </div>
          )}
          <Link
            to="/notifications"
            className="mt-2 block rounded-md p-2 text-center text-sm text-primary hover:bg-accent"
            onClick={() => setOpen(false)}
          >
            View all
          </Link>
        </div>
      )}
    </div>
  )
}
