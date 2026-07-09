import { Badge } from '@/components/ui/badge'
import { STATUS_LABELS } from '@/utils/constants'

const VARIANTS = { want: 'outline', in_progress: 'secondary', completed: 'default', dropped: 'outline' }

export function StatusBadge({ status }) {
  return <Badge variant={VARIANTS[status] ?? 'outline'}>{STATUS_LABELS[status] ?? status}</Badge>
}
