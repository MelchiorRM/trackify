import { Compass } from 'lucide-react'
import { Link, useNavigate } from 'react-router-dom'

import { logout as logoutRequest } from '@/api/auth'
import { Button } from '@/components/ui/button'
import { useAuthStore } from '@/store/authStore'

export default function Navbar() {
  const user = useAuthStore((s) => s.user)
  const clearAuth = useAuthStore((s) => s.clearAuth)
  const navigate = useNavigate()

  const handleLogout = async () => {
    await logoutRequest()
    clearAuth()
    navigate('/login')
  }

  return (
    <nav className="sticky top-0 z-10 border-b bg-background/80 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-5xl items-center justify-between px-4">
        <Link to="/" className="flex items-center gap-2 text-lg font-bold tracking-tight">
          <Compass className="h-5 w-5 text-primary" />
          Trackify
        </Link>
        {/* Global search bar lands in Phase 2 once GET /search exists */}
        <div className="flex items-center gap-3">
          {user ? (
            <>
              <span className="text-sm text-muted-foreground">{user.username}</span>
              <Button onClick={handleLogout} variant="outline" size="sm">
                Log out
              </Button>
            </>
          ) : (
            <>
              <Button asChild variant="ghost" size="sm">
                <Link to="/login">Log in</Link>
              </Button>
              <Button asChild size="sm">
                <Link to="/register">Register</Link>
              </Button>
            </>
          )}
        </div>
      </div>
    </nav>
  )
}
