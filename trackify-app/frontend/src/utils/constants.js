import { BookOpen, Film, Music2 } from 'lucide-react'

export const DOMAINS = ['movie', 'book', 'music']

export const DOMAIN_LABELS = {
  movie: 'Movies',
  book: 'Books',
  music: 'Music',
}

export const DOMAIN_ICONS = {
  movie: Film,
  book: BookOpen,
  music: Music2,
}

// Validated categorical palette (fixed order = the CVD-safety mechanism —
// see the dataviz skill's color-formula.md). Used anywhere a domain needs a
// consistent chart color (Stats page charts).
export const DOMAIN_CHART_COLORS = {
  movie: '#2a78d6',
  book: '#1baf7a',
  music: '#eda100',
}

// Shared recharts axis/label styling, used by every Stats chart so they
// read as one system rather than drifting independently.
export const CHART_AXIS_LINE_STYLE = { stroke: '#c3c2b7' }
export const CHART_TICK_STYLE = { fill: '#898781', fontSize: 12 }
export const CHART_LABEL_FILL = '#52514e'

export const STATUSES = ['want', 'in_progress', 'completed', 'dropped']

export const STATUS_LABELS = {
  want: 'Want',
  in_progress: 'In Progress',
  completed: 'Completed',
  dropped: 'Dropped',
}
