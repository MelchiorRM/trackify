import { Loader2 } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Route, Routes } from 'react-router-dom'

import { fetchMe } from '@/api/auth'
import { apiClient } from '@/api/client'
import Navbar from '@/components/layout/Navbar'
import Home from '@/pages/Home'
import Login from '@/pages/Login'
import NotFound from '@/pages/NotFound'
import Register from '@/pages/Register'
import { useAuthStore } from '@/store/authStore'

export default function App() {
  const setAuth = useAuthStore((s) => s.setAuth)
  const [checkingSession, setCheckingSession] = useState(true)

  // Access token lives only in memory, so a hard page reload loses it.
  // Restore the session here via the httpOnly refresh cookie before
  // rendering routes — this is what makes "reload and stay logged in" work.
  useEffect(() => {
    let cancelled = false

    const restoreSession = async () => {
      try {
        const { data } = await apiClient.post('/auth/refresh')
        useAuthStore.getState().setAccessToken(data.access_token)
        const user = await fetchMe()
        if (!cancelled) setAuth({ user, accessToken: data.access_token })
      } catch {
        // No valid refresh cookie — staying logged out is correct here,
        // not an error worth surfacing.
      } finally {
        if (!cancelled) setCheckingSession(false)
      }
    }

    restoreSession()
    return () => {
      cancelled = true
    }
  }, [setAuth])

  if (checkingSession) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    )
  }

  return (
    <>
      <Navbar />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </>
  )
}
