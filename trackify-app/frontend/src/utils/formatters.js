export function formatDate(value) {
  if (!value) return ''
  return new Date(value).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })
}

export function formatRating(rating) {
  return rating == null ? '—' : rating.toFixed(1)
}
