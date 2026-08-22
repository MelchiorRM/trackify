import { Mail } from 'lucide-react'
import { Link } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import { useUnreadMessageCount } from '@/hooks/useMessages'

export function MessageBell() {
  const { data } = useUnreadMessageCount()
  const count = data?.count ?? 0

  return (
    <Button asChild variant="ghost" size="icon" className="relative">
      <Link to="/messages" aria-label="Messages">
        <Mail className="h-5 w-5" />
        {count > 0 && (
          <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-destructive px-1 text-[10px] font-medium text-destructive-foreground">
            {count > 9 ? '9+' : count}
          </span>
        )}
      </Link>
    </Button>
  )
}
