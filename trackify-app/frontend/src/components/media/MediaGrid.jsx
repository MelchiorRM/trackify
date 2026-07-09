import { MediaCard } from './MediaCard'

export function MediaGrid({ items, onAdd, isItemInLibrary, addingExternalId }) {
  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
      {items.map((item) => (
        <MediaCard
          key={`${item.domain}-${item.external_id}`}
          item={item}
          onAdd={onAdd ? () => onAdd(item) : undefined}
          inLibrary={isItemInLibrary?.(item)}
          isAdding={addingExternalId === item.external_id}
        />
      ))}
    </div>
  )
}
