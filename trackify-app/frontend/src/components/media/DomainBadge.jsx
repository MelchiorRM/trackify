import { Badge } from '@/components/ui/badge'
import { DOMAIN_ICONS } from '@/utils/constants'

const LABELS = { movie: 'Movie', book: 'Book', music: 'Music' }

export function DomainBadge({ domain, className }) {
  const Icon = DOMAIN_ICONS[domain]
  return (
    <Badge variant="secondary" className={className}>
      {Icon && <Icon className="mr-1 h-3 w-3" />}
      {LABELS[domain] ?? domain}
    </Badge>
  )
}
