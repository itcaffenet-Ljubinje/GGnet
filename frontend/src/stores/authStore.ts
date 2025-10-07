import { create } from 'zustand'
// import { persist } from 'zustand/middleware' // Unused for now
import { api } from '../lib/api'

export interface User {
  id: number
  username: string
  email?: string
  full_name?: string
  role: 'admin' | 'operator' | 'viewer'
  status: 'active' | 'inactive' | 'suspended'
  is_active: boolean
  created_at: string
  last_login?: string
}

interface AuthState {
  user: User | null
  accessToken: string | null
  refreshToken: string | null
  isAuthenticated: boolean
  isLoading: boolean
}

interface AuthActions {
  login: (username: string, password: string) => Promise<boolean>
  logout: () => void
  refreshAuth: () => Promise<boolean>
  setUser: (user: User) => void
  clearAuth: () => void
}

type AuthStore = AuthState & AuthActions

export const useAuthStore = create<AuthStore>()(
  (set, get) => ({
      // State
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: false,

      // Actions
      login: async (username: string, password: string) => {
        set({ isLoading: true })
        
        try {
          const response = await api.post('/api/auth/login', {
            username,
            password,
          })

          const { access_token, refresh_token } = response.data

          // Set tokens in API client
          api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`

          // Get user info
          const userResponse = await api.get('/api/auth/me')
          const user = userResponse.data

          set({
            user,
            accessToken: access_token,
            refreshToken: refresh_token,
            isAuthenticated: true,
            isLoading: false,
          })

          return true
        } catch (error: unknown) {
          set({ isLoading: false })
          return false
        }
      },

      logout: async () => {
        const { accessToken } = get()
        
        try {
          if (accessToken) {
            await api.post('/api/auth/logout')
          }
        } catch (error) {
          // Ignore logout errors
          console.warn('Logout request failed:', error)
        }

        // Clear auth state
        delete api.defaults.headers.common['Authorization']
        
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
          isLoading: false,
        })
      },

      refreshAuth: async () => {
        const { refreshToken } = get()
        
        if (!refreshToken) {
          get().clearAuth()
          return false
        }

        try {
          const response = await api.post('/api/auth/refresh', {
            refresh_token: refreshToken,
          })

          const { access_token, refresh_token: new_refresh_token } = response.data

          // Update tokens
          api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`

          set({
            accessToken: access_token,
            refreshToken: new_refresh_token,
          })

          return true
        } catch (error) {
          console.warn('Token refresh failed:', error)
          get().clearAuth()
          return false
        }
      },

      setUser: (user: User) => {
        set({ user })
      },

      clearAuth: () => {
        delete api.defaults.headers.common['Authorization']
        
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
          isLoading: false,
        })
      },
    })
)

