import { BookOpen, Film, Music2 } from 'lucide-react'

import { Badge } from '@/components/ui/badge'

const ICONS = { movie: Film, book: BookOpen, music: Music2 }
const LABELS = { movie: 'Movie', book: 'Book', music: 'Music' }

export function DomainBadge({ domain, className }) {
  const Icon = ICONS[domain]
  return (
    <Badge variant="secondary" className={className}>
      {Icon && <Icon className="mr-1 h-3 w-3" />}
      {LABELS[domain] ?? domain}
    </Badge>
  )
}
