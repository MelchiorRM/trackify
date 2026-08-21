export function formatDate(value) {
  if (!value) return ''
  return new Date(value).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })
}

export function formatRating(rating) {
  return rating == null ? '—' : rating.toFixed(1)
}

export function formatMonth(monthKey) {
  const [year, month] = monthKey.split('-').map(Number)
  return new Date(year, month - 1, 1).toLocaleDateString(undefined, { month: 'short', year: 'numeric' })
}
