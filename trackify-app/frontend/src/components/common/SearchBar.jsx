import { Search } from 'lucide-react'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { Input } from '@/components/ui/input'

export function SearchBar() {
  const [value, setValue] = useState('')
  const navigate = useNavigate()

  const handleSubmit = (e) => {
    e.preventDefault()
    if (value.trim()) navigate(`/search?q=${encodeURIComponent(value.trim())}`)
  }

  return (
    <form onSubmit={handleSubmit} className="relative w-full max-w-sm">
      <Search className="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
      <Input
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder="Search movies, books, music..."
        className="pl-8"
      />
    </form>
  )
}
