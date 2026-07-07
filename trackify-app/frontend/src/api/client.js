import axios from 'axios'

import { useAuthStore } from '../store/authStore'

const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const apiClient = axios.create({
  baseURL,
  withCredentials: true, // sends the httpOnly refresh_token cookie
})

apiClient.interceptors.request.use((config) => {
  const { accessToken } = useAuthStore.getState()
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`
  }
  return config
})

// Dedupe concurrent refreshes: if five requests 401 at once, only one
// /auth/refresh call should fire.
let refreshPromise = null

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const { config, response } = error
    if (response?.status !== 401 || config._retried) {
      throw error
    }
    config._retried = true

    refreshPromise ??= axios
      .post(`${baseURL}/auth/refresh`, {}, { withCredentials: true })
      .finally(() => {
        refreshPromise = null
      })

    try {
      const { data } = await refreshPromise
      useAuthStore.getState().setAccessToken(data.access_token)
      config.headers.Authorization = `Bearer ${data.access_token}`
      return apiClient(config)
    } catch (refreshError) {
      useAuthStore.getState().clearAuth()
      throw refreshError
    }
  },
)
