import { Link } from 'react-router-dom'

export function FavoritesRow({ favorites }) {
  if (favorites.length === 0) {
    return null
  }

  return (
    <div className="flex gap-3">
      {favorites.map((favorite) => (
        <Link
          key={favorite.id}
          to={`/item/${favorite.item.domain}/${favorite.item.external_id}`}
          title={favorite.item.title}
          className="flex h-28 w-20 flex-shrink-0 items-center justify-center overflow-hidden rounded-lg bg-muted shadow-sm transition hover:opacity-90"
        >
          {favorite.item.cover_url ? (
            <img src={favorite.item.cover_url} alt={favorite.item.title} className="h-full w-full object-cover" />
          ) : (
            <span className="px-1 text-center text-[10px] text-muted-foreground">{favorite.item.title}</span>
          )}
        </Link>
      ))}
    </div>
  )
}
