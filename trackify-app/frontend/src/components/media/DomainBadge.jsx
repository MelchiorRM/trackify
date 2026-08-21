import { Badge } from '@/components/ui/badge'
import { DOMAIN_ICONS, DOMAIN_LABELS } from '@/utils/constants'

export function DomainBadge({ domain, className }) {
  const Icon = DOMAIN_ICONS[domain]
  return (
    <Badge variant="secondary" className={className}>
      {Icon && <Icon className="mr-1 h-3 w-3" />}
      {DOMAIN_LABELS[domain] ?? domain}
    </Badge>
  )
}
