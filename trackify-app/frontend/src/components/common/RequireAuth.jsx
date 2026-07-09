import { Navigate } from 'react-router-dom'

import { useAuthStore } from '@/store/authStore'

export function RequireAuth({ children }) {
  const user = useAuthStore((s) => s.user)
  return user ? children : <Navigate to="/login" replace />
}
