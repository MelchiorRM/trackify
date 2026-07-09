import { Badge } from '@/components/ui/badge'
import { formatDate } from '@/utils/formatters'

export function DiaryList({ entries, onDelete }) {
  if (entries.length === 0) {
    return <p className="text-sm text-muted-foreground">No sessions logged yet.</p>
  }

  return (
    <ul className="space-y-2">
      {entries.map((entry) => (
        <li key={entry.id} className="flex items-center justify-between rounded-lg border p-3 text-sm">
          <div className="flex items-center gap-2">
            <span className="font-medium">{formatDate(entry.logged_at)}</span>
            {entry.rewatch && <Badge variant="outline">Rewatch</Badge>}
            {entry.rating != null && <span className="text-muted-foreground">★ {entry.rating}</span>}
            {entry.note && <span className="text-muted-foreground">— {entry.note}</span>}
          </div>
          {onDelete && (
            <button onClick={() => onDelete(entry.id)} className="text-muted-foreground hover:text-destructive">
              Delete
            </button>
          )}
        </li>
      ))}
    </ul>
  )
}
