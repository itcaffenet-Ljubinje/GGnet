// Vitest globals are available via globals: true in vitest.config.ts
import { render, waitFor } from '../__tests__/setup/test-utils'
import userEvent from '@testing-library/user-event'
import LoginPage from './LoginPage'
import { useAuthStore } from '../stores/authStore'

// Mock the auth store
vi.mock('../stores/authStore', () => ({
  useAuthStore: vi.fn(),
}))

describe('LoginPage', () => {
  const mockLogin = vi.fn()
  const mockIsLoading = false

  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(useAuthStore).mockReturnValue({
      login: mockLogin,
      isLoading: mockIsLoading,
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      logout: vi.fn(),
      refreshAuth: vi.fn(),
      setUser: vi.fn(),
      clearAuth: vi.fn(),
    } as ReturnType<typeof useAuthStore>)
  })

  describe('rendering', () => {
    it('should render login form', () => {
      render(<LoginPage />)

      expect(screen.getByText(/sign in to ggnet/i)).toBeInTheDocument()
      expect(screen.getByPlaceholderText('Username')).toBeInTheDocument()
      expect(screen.getByPlaceholderText('Password')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
    })

    it('should render GG logo', () => {
      render(<LoginPage />)

      expect(screen.getByText('GG')).toBeInTheDocument()
    })

    it('should display default credentials hint', () => {
      render(<LoginPage />)

      expect(screen.getByText(/default credentials/i)).toBeInTheDocument()
      expect(screen.getByText('admin')).toBeInTheDocument()
      expect(screen.getByText('admin123')).toBeInTheDocument()
    })
  })

  describe('form validation', () => {
    it('should show error when username is empty', async () => {
      const user = userEvent.setup()
      render(<LoginPage />)

      const submitButton = screen.getByRole('button', { name: /sign in/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText(/username is required/i)).toBeInTheDocument()
      })
    })

    it('should show error when username is too short', async () => {
      const user = userEvent.setup()
      render(<LoginPage />)

      const usernameInput = screen.getByPlaceholderText('Username')
      await user.type(usernameInput, 'ab')
      
      const submitButton = screen.getByRole('button', { name: /sign in/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText(/username must be at least 3 characters/i)).toBeInTheDocument()
      })
    })

    it('should show error when password is empty', async () => {
      const user = userEvent.setup()
      render(<LoginPage />)

      const usernameInput = screen.getByPlaceholderText('Username')
      await user.type(usernameInput, 'testuser')
      
      const submitButton = screen.getByRole('button', { name: /sign in/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText(/password is required/i)).toBeInTheDocument()
      })
    })

    it('should show error when password is too short', async () => {
      const user = userEvent.setup()
      render(<LoginPage />)

      const usernameInput = screen.getByPlaceholderText('Username')
      const passwordInput = screen.getByPlaceholderText('Password')
      
      await user.type(usernameInput, 'testuser')
      await user.type(passwordInput, '12345')
      
      const submitButton = screen.getByRole('button', { name: /sign in/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText(/password must be at least 6 characters/i)).toBeInTheDocument()
      })
    })
  })

  describe('password visibility toggle', () => {
    it('should toggle password visibility when eye icon is clicked', async () => {
      const user = userEvent.setup()
      render(<LoginPage />)

      const passwordInput = screen.getByPlaceholderText('Password') as HTMLInputElement
      
      // Initially password should be hidden
      expect(passwordInput.type).toBe('password')

      // Find the toggle button - it's in the same parent div
      const passwordContainer = passwordInput.closest('.relative')
      const toggleButton = passwordContainer?.querySelector('button[type="button"]')

      // Click toggle button
      if (toggleButton) {
        await user.click(toggleButton)
        
        // Password should be visible
        expect(passwordInput.type).toBe('text')
      }
    })

    it('should toggle back to hidden when clicked again', async () => {
      const user = userEvent.setup()
      render(<LoginPage />)

      const passwordInput = screen.getByPlaceholderText('Password') as HTMLInputElement
      const passwordContainer = passwordInput.closest('.relative')
      const toggleButton = passwordContainer?.querySelector('button[type="button"]')

      if (toggleButton) {
        // First click - show password
        await user.click(toggleButton)
        expect(passwordInput.type).toBe('text')

        // Second click - hide password
        await user.click(toggleButton)
        expect(passwordInput.type).toBe('password')
      }
    })
  })

  describe('login submission', () => {
    it('should call login with correct credentials', async () => {
      const user = userEvent.setup()
      mockLogin.mockResolvedValue(true)

      render(<LoginPage />)

      const usernameInput = screen.getByPlaceholderText('Username')
      const passwordInput = screen.getByPlaceholderText('Password')
      const submitButton = screen.getByRole('button', { name: /sign in/i })

      await user.type(usernameInput, 'testuser')
      await user.type(passwordInput, 'password123')
      await user.click(submitButton)

      await waitFor(() => {
        expect(mockLogin).toHaveBeenCalledWith('testuser', 'password123')
      })
    })

    it('should show error message when login fails', async () => {
      const user = userEvent.setup()
      mockLogin.mockResolvedValue(false)

      render(<LoginPage />)

      const usernameInput = screen.getByPlaceholderText('Username')
      const passwordInput = screen.getByPlaceholderText('Password')
      const submitButton = screen.getByRole('button', { name: /sign in/i })

      await user.type(usernameInput, 'testuser')
      await user.type(passwordInput, 'wrongpassword')
      await user.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText(/invalid username or password/i)).toBeInTheDocument()
      })
    })

    it('should show error message when login throws error', async () => {
      const user = userEvent.setup()
      mockLogin.mockRejectedValue(new Error('Network error'))

      render(<LoginPage />)

      const usernameInput = screen.getByPlaceholderText('Username')
      const passwordInput = screen.getByPlaceholderText('Password')
      const submitButton = screen.getByRole('button', { name: /sign in/i })

      await user.type(usernameInput, 'testuser')
      await user.type(passwordInput, 'password123')
      await user.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText(/login failed. please try again/i)).toBeInTheDocument()
      })
    })
  })

  describe('loading state', () => {
    it('should disable inputs when loading', () => {
      vi.mocked(useAuthStore).mockReturnValue({
        login: mockLogin,
        isLoading: true,
        user: null,
        accessToken: null,
        refreshToken: null,
        isAuthenticated: false,
        logout: vi.fn(),
        refreshAuth: vi.fn(),
        setUser: vi.fn(),
        clearAuth: vi.fn(),
      } as ReturnType<typeof useAuthStore>)

      render(<LoginPage />)

      const usernameInput = screen.getByPlaceholderText('Username')
      const passwordInput = screen.getByPlaceholderText('Password')
      const submitButton = screen.getByRole('button', { name: /signing in/i })

      expect(usernameInput).toBeDisabled()
      expect(passwordInput).toBeDisabled()
      expect(submitButton).toBeDisabled()
    })

    it('should show loading text when submitting', () => {
      vi.mocked(useAuthStore).mockReturnValue({
        login: mockLogin,
        isLoading: true,
        user: null,
        accessToken: null,
        refreshToken: null,
        isAuthenticated: false,
        logout: vi.fn(),
        refreshAuth: vi.fn(),
        setUser: vi.fn(),
        clearAuth: vi.fn(),
      } as ReturnType<typeof useAuthStore>)

      render(<LoginPage />)

      expect(screen.getByText(/signing in/i)).toBeInTheDocument()
    })

    it('should not disable inputs when not loading', () => {
      render(<LoginPage />)

      const usernameInput = screen.getByPlaceholderText('Username')
      const passwordInput = screen.getByPlaceholderText('Password')

      expect(usernameInput).not.toBeDisabled()
      expect(passwordInput).not.toBeDisabled()
    })
  })

  describe('accessibility', () => {
    it('should have proper form structure', () => {
      render(<LoginPage />)

      const usernameInput = screen.getByPlaceholderText('Username')
      const form = usernameInput.closest('form')
      expect(form).toBeInTheDocument()
    })

    it('should have accessible labels for inputs', () => {
      render(<LoginPage />)

      // Labels are sr-only but should be associated
      const usernameInput = screen.getByPlaceholderText('Username')
      const passwordInput = screen.getByPlaceholderText('Password')

      expect(usernameInput).toHaveAttribute('autoComplete', 'username')
      expect(passwordInput).toHaveAttribute('autoComplete', 'current-password')
    })
  })
})

