import { Link } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'

import { DomainBadge } from './DomainBadge'

export function MediaCard({ item, onAdd, isAdding, inLibrary }) {
  const itemHref = `/item/${item.domain}/${item.external_id}`

  return (
    <Card className="flex flex-col overflow-hidden">
      <Link to={itemHref} className="block">
        <div className="flex aspect-[2/3] w-full items-center justify-center bg-muted">
          {item.cover_url ? (
            <img src={item.cover_url} alt={item.title} className="h-full w-full object-cover" />
          ) : (
            <span className="text-xs text-muted-foreground">No cover</span>
          )}
        </div>
      </Link>
      <div className="flex flex-1 flex-col gap-1 p-3">
        <DomainBadge domain={item.domain} className="self-start" />
        <Link to={itemHref} className="line-clamp-2 font-medium hover:underline">
          {item.title}
        </Link>
        {item.creator && <p className="line-clamp-1 text-sm text-muted-foreground">{item.creator}</p>}
        {onAdd && (
          <Button
            size="sm"
            variant={inLibrary ? 'outline' : 'default'}
            disabled={inLibrary || isAdding}
            onClick={onAdd}
            className="mt-2"
          >
            {inLibrary ? 'In library' : 'Add to library'}
          </Button>
        )}
      </div>
    </Card>
  )
}
