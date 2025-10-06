import { render, screen } from '@testing-library/react'
import App from './App'

// Mock the auth store
vi.mock('./stores/authStore', () => ({
  useAuthStore: () => ({
    isAuthenticated: false,
    user: null,
    login: vi.fn(),
    logout: vi.fn(),
  }),
}))

// Mock react-router-dom
vi.mock('react-router-dom', () => ({
  Routes: ({ children }: { children: React.ReactNode }) => <div data-testid="routes">{children}</div>,
  Route: ({ element }: { element: React.ReactNode }) => <div data-testid="route">{element}</div>,
  Navigate: () => <div data-testid="navigate">Navigate</div>,
  useLocation: () => ({ pathname: '/' }),
}))

// Mock components
vi.mock('./components/Layout', () => ({
  default: ({ children }: { children: React.ReactNode }) => <div data-testid="layout">{children}</div>,
}))

vi.mock('./components/ErrorBoundary', () => ({
  ErrorBoundary: ({ children }: { children: React.ReactNode }) => <div data-testid="error-boundary">{children}</div>,
}))

vi.mock('./components/notifications', () => ({
  NotificationProvider: ({ children }: { children: React.ReactNode }) => <div data-testid="notifications">{children}</div>,
}))

// Mock recharts-heavy components
vi.mock('./components/SystemMonitor', () => ({
  default: () => <div data-testid="system-monitor">System Monitor</div>,
}))

// Mock recharts directly to avoid Vite resolving it
vi.mock('recharts', () => ({
  BarChart: () => null,
  Bar: () => null,
  XAxis: () => null,
  YAxis: () => null,
  Tooltip: () => null,
  Legend: () => null,
}))

vi.mock('./pages/LoginPage', () => ({
  default: () => <div data-testid="login-page">Login Page</div>,
}))

describe('App', () => {
  it('renders without crashing', () => {
    render(<App />)
    expect(screen.getByTestId('error-boundary')).toBeInTheDocument()
  })

  it('shows login page when not authenticated', () => {
    render(<App />)
    expect(screen.getByTestId('login-page')).toBeInTheDocument()
  })
})
