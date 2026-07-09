export function ProgressBar({ progress, total }) {
  if (!total) return null
  const pct = Math.min(100, Math.round(((progress ?? 0) / total) * 100))

  return (
    <div className="space-y-1">
      <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
        <div className="h-full bg-primary transition-all" style={{ width: `${pct}%` }} />
      </div>
      <p className="text-xs text-muted-foreground">
        {progress ?? 0} / {total}
      </p>
    </div>
  )
}
