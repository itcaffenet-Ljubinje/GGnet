// Vitest globals are available via globals: true in vitest.config.ts
import { useAuthStore } from './authStore'
import { api } from '../lib/api'
import type { User } from './authStore'
import type { AxiosResponse } from 'axios'

// Helper type for mocked API responses
type MockAxiosResponse<T> = Partial<AxiosResponse<T>>

// Mock the API module
vi.mock('../lib/api', () => ({
  api: {
    post: vi.fn(),
    get: vi.fn(),
    defaults: {
      headers: {
        common: {} as Record<string, string>,
      },
    },
  },
}))

describe('authStore', () => {
  beforeEach(() => {
    // Reset store state before each test
    const store = useAuthStore.getState()
    store.clearAuth()
    
    // Clear all mocks
    vi.clearAllMocks()
    
    // Reset API defaults
    delete api.defaults.headers.common['Authorization']
  })

  describe('initial state', () => {
    it('should have initial state with no user', () => {
      const store = useAuthStore.getState()
      
      expect(store.user).toBeNull()
      expect(store.accessToken).toBeNull()
      expect(store.refreshToken).toBeNull()
      expect(store.isAuthenticated).toBe(false)
      expect(store.isLoading).toBe(false)
    })
  })

  describe('login', () => {
    it('should successfully login with valid credentials', async () => {
      const mockUser: User = {
        id: 1,
        username: 'testuser',
        email: 'test@example.com',
        role: 'admin',
        status: 'active',
        is_active: true,
        created_at: '2024-01-01T00:00:00Z',
      }

      const mockTokens = {
        access_token: 'access-token-123',
        refresh_token: 'refresh-token-456',
      }

      // Mock API responses
      vi.mocked(api.post).mockResolvedValueOnce({
        data: mockTokens,
      } as MockAxiosResponse<typeof mockTokens>)

      vi.mocked(api.get).mockResolvedValueOnce({
        data: mockUser,
      } as MockAxiosResponse<User>)

      const result = await useAuthStore.getState().login('testuser', 'password123')

      expect(result).toBe(true)
      
      // Get fresh state after login
      const state = useAuthStore.getState()
      expect(state.user).toEqual(mockUser)
      expect(state.accessToken).toBe('access-token-123')
      expect(state.refreshToken).toBe('refresh-token-456')
      expect(state.isAuthenticated).toBe(true)
      expect(state.isLoading).toBe(false)
      expect(api.defaults.headers.common['Authorization']).toBe('Bearer access-token-123')
    })

    it('should set isLoading to true during login', async () => {
      // Create a promise that we can control
      let resolveLogin: (value: MockAxiosResponse<{ access_token: string; refresh_token: string }>) => void
      const loginPromise = new Promise<MockAxiosResponse<{ access_token: string; refresh_token: string }>>((resolve) => {
        resolveLogin = resolve
      })

      vi.mocked(api.post).mockReturnValueOnce(loginPromise as Promise<MockAxiosResponse<unknown>>)

      const loginPromise2 = useAuthStore.getState().login('testuser', 'password123')

      // Check loading state immediately
      expect(useAuthStore.getState().isLoading).toBe(true)

      // Resolve the promise
      resolveLogin!({
        data: {
          access_token: 'token',
          refresh_token: 'refresh',
        },
      })

      vi.mocked(api.get).mockResolvedValueOnce({
        data: { id: 1, username: 'testuser', role: 'admin', status: 'active', is_active: true, created_at: '2024-01-01' },
      } as MockAxiosResponse<User>)

      await loginPromise2

      expect(useAuthStore.getState().isLoading).toBe(false)
    })

    it('should return false on login failure', async () => {
      vi.mocked(api.post).mockRejectedValueOnce(new Error('Invalid credentials') as unknown)

      const store = useAuthStore.getState()
      const result = await store.login('testuser', 'wrongpassword')

      expect(result).toBe(false)
      expect(store.user).toBeNull()
      expect(store.isAuthenticated).toBe(false)
      expect(store.isLoading).toBe(false)
    })

    it('should handle network errors during login', async () => {
      vi.mocked(api.post).mockRejectedValueOnce(new Error('Network error') as unknown)

      const store = useAuthStore.getState()
      const result = await store.login('testuser', 'password123')

      expect(result).toBe(false)
      expect(store.isAuthenticated).toBe(false)
    })

    it('should handle errors when fetching user info', async () => {
      vi.mocked(api.post).mockResolvedValueOnce({
        data: {
          access_token: 'token',
          refresh_token: 'refresh',
        },
      } as MockAxiosResponse<{ access_token: string; refresh_token: string }>)

      vi.mocked(api.get).mockRejectedValueOnce(new Error('Failed to fetch user') as unknown)

      const store = useAuthStore.getState()
      const result = await store.login('testuser', 'password123')

      expect(result).toBe(false)
      expect(store.isAuthenticated).toBe(false)
    })
  })

  describe('logout', () => {
    it('should clear auth state on logout', async () => {
      // First login
      const mockUser: User = {
        id: 1,
        username: 'testuser',
        role: 'admin',
        status: 'active',
        is_active: true,
        created_at: '2024-01-01T00:00:00Z',
      }

      vi.mocked(api.post).mockResolvedValueOnce({
        data: { access_token: 'token', refresh_token: 'refresh' },
      } as MockAxiosResponse<{ access_token: string; refresh_token: string }>)

      vi.mocked(api.get).mockResolvedValueOnce({
        data: mockUser,
      } as MockAxiosResponse<User>)

      const store = useAuthStore.getState()
      await store.login('testuser', 'password123')

      // Set authorization header
      api.defaults.headers.common['Authorization'] = 'Bearer token'

      // Mock logout API call
      vi.mocked(api.post).mockResolvedValueOnce({
        data: {},
      } as MockAxiosResponse<Record<string, never>>)

      // Logout
      await store.logout()

      expect(store.user).toBeNull()
      expect(store.accessToken).toBeNull()
      expect(store.refreshToken).toBeNull()
      expect(store.isAuthenticated).toBe(false)
      expect(store.isLoading).toBe(false)
      expect(api.defaults.headers.common['Authorization']).toBeUndefined()
    })

    it('should call logout API when accessToken exists', async () => {
      const store = useAuthStore.getState()
      
      // Set tokens manually
      store.setUser({
        id: 1,
        username: 'testuser',
        role: 'admin',
        status: 'active',
        is_active: true,
        created_at: '2024-01-01T00:00:00Z',
      })
      
      // Use direct state update for testing
      useAuthStore.setState({
        accessToken: 'token',
        isAuthenticated: true,
      })

      vi.mocked(api.post).mockResolvedValueOnce({
        data: {},
      } as MockAxiosResponse<Record<string, never>>)

      await store.logout()

      expect(api.post).toHaveBeenCalledWith('/api/auth/logout')
    })

    it('should logout even if API call fails', async () => {
      const store = useAuthStore.getState()
      
      useAuthStore.setState({
        accessToken: 'token',
        isAuthenticated: true,
      })

      const consoleWarnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})

      vi.mocked(api.post).mockRejectedValueOnce(new Error('Network error') as unknown)

      await store.logout()

      expect(store.isAuthenticated).toBe(false)
      expect(consoleWarnSpy).toHaveBeenCalled()

      consoleWarnSpy.mockRestore()
    })

    it('should logout without calling API if no accessToken', async () => {
      const store = useAuthStore.getState()
      
      useAuthStore.setState({
        isAuthenticated: true,
        accessToken: null,
      })

      await store.logout()

      expect(api.post).not.toHaveBeenCalled()
      expect(store.isAuthenticated).toBe(false)
    })
  })

  describe('refreshAuth', () => {
    it('should successfully refresh tokens', async () => {
      useAuthStore.setState({
        refreshToken: 'old-refresh-token',
      })

      vi.mocked(api.post).mockResolvedValueOnce({
        data: {
          access_token: 'new-access-token',
          refresh_token: 'new-refresh-token',
        },
      } as MockAxiosResponse<{ access_token: string; refresh_token: string }>)

      const result = await useAuthStore.getState().refreshAuth()

      expect(result).toBe(true)
      const state = useAuthStore.getState()
      expect(state.accessToken).toBe('new-access-token')
      expect(state.refreshToken).toBe('new-refresh-token')
      expect(api.defaults.headers.common['Authorization']).toBe('Bearer new-access-token')
    })

    it('should return false and clear auth if no refreshToken', async () => {
      const store = useAuthStore.getState()
      
      useAuthStore.setState({
        refreshToken: null,
      })

      const result = await store.refreshAuth()

      expect(result).toBe(false)
      expect(store.isAuthenticated).toBe(false)
    })

    it('should clear auth on refresh failure', async () => {
      const store = useAuthStore.getState()
      
      useAuthStore.setState({
        refreshToken: 'invalid-token',
        isAuthenticated: true,
      })

      const consoleWarnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})

      vi.mocked(api.post).mockRejectedValueOnce(new Error('Token expired') as unknown)

      const result = await store.refreshAuth()

      expect(result).toBe(false)
      expect(store.isAuthenticated).toBe(false)
      expect(consoleWarnSpy).toHaveBeenCalled()

      consoleWarnSpy.mockRestore()
    })
  })

  describe('setUser', () => {
    it('should update user in state', () => {
      const newUser: User = {
        id: 2,
        username: 'newuser',
        email: 'new@example.com',
        role: 'operator',
        status: 'active',
        is_active: true,
        created_at: '2024-01-02T00:00:00Z',
      }

      useAuthStore.getState().setUser(newUser)

      expect(useAuthStore.getState().user).toEqual(newUser)
    })
  })

  describe('clearAuth', () => {
    it('should clear all auth state', () => {
      const store = useAuthStore.getState()
      
      // Set some state first
      useAuthStore.setState({
        user: { id: 1, username: 'test', role: 'admin', status: 'active', is_active: true, created_at: '2024-01-01' },
        accessToken: 'token',
        refreshToken: 'refresh',
        isAuthenticated: true,
      })

      api.defaults.headers.common['Authorization'] = 'Bearer token'

      store.clearAuth()

      expect(store.user).toBeNull()
      expect(store.accessToken).toBeNull()
      expect(store.refreshToken).toBeNull()
      expect(store.isAuthenticated).toBe(false)
      expect(store.isLoading).toBe(false)
      expect(api.defaults.headers.common['Authorization']).toBeUndefined()
    })
  })
})

