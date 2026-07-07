import { create } from 'zustand'

// Access token lives in memory only (not localStorage) — see appPlan.txt
// AUTH FLOW. It's lost on a full page reload by design; App.jsx restores it
// via POST /auth/refresh, which relies on the httpOnly refresh cookie.
export const useAuthStore = create((set) => ({
  user: null,
  accessToken: null,
  setAuth: ({ user, accessToken }) => set({ user, accessToken }),
  setAccessToken: (accessToken) => set({ accessToken }),
  clearAuth: () => set({ user: null, accessToken: null }),
}))
