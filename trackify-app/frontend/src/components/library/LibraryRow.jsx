import { Link } from 'react-router-dom'

import { DomainBadge } from '@/components/media/DomainBadge'
import { Button } from '@/components/ui/button'

import { ProgressBar } from './ProgressBar'
import { StatusPicker } from './StatusPicker'

export function LibraryRow({ entry, onStatusChange, onRemove, isUpdating }) {
  const { item } = entry

  return (
    <div className="flex items-center gap-4 rounded-lg border p-3">
      <div className="flex h-20 w-14 flex-shrink-0 items-center justify-center overflow-hidden rounded bg-muted">
        {item.cover_url ? (
          <img src={item.cover_url} alt={item.title} className="h-full w-full object-cover" />
        ) : (
          <span className="text-[10px] text-muted-foreground">No cover</span>
        )}
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <DomainBadge domain={item.domain} />
          <Link to={`/item/${item.domain}/${item.external_id}`} className="truncate font-medium hover:underline">
            {item.title}
          </Link>
        </div>
        {entry.progress_total ? (
          <div className="mt-2 max-w-xs">
            <ProgressBar progress={entry.progress} total={entry.progress_total} />
          </div>
        ) : null}
      </div>
      <StatusPicker value={entry.status} disabled={isUpdating} onChange={onStatusChange} />
      <Button variant="ghost" size="sm" onClick={onRemove}>
        Remove
      </Button>
    </div>
  )
}
