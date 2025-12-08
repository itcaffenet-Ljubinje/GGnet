/**
 * Test Utilities
 * 
 * Custom render function and test utilities for React components
 * Provides all necessary providers (Router, QueryClient, etc.)
 */

import { ReactElement } from 'react'
import { render, RenderOptions } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ErrorBoundary } from '../../components/ErrorBoundary'
import { NotificationProvider } from '../../components/notifications'

// Create a test QueryClient with default options
const createTestQueryClient = () => {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0, // gcTime replaces cacheTime in React Query v5
      },
      mutations: {
        retry: false,
      },
    },
  })
}

interface AllTheProvidersProps {
  children: React.ReactNode
  queryClient?: QueryClient
}

function AllTheProviders({ children, queryClient }: AllTheProvidersProps) {
  const client = queryClient || createTestQueryClient()

  return (
    <QueryClientProvider client={client}>
      <BrowserRouter>
        <ErrorBoundary>
          <NotificationProvider>
            {children}
          </NotificationProvider>
        </ErrorBoundary>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  queryClient?: QueryClient
}

/**
 * Custom render function that includes all necessary providers
 * 
 * @example
 * ```tsx
 * const { getByText } = render(<MyComponent />)
 * ```
 */
function customRender(
  ui: ReactElement,
  options?: CustomRenderOptions
) {
  const { queryClient, ...renderOptions } = options || {}

  return render(ui, {
    wrapper: (props) => (
      <AllTheProviders {...props} queryClient={queryClient} />
    ),
    ...renderOptions,
  })
}

// Re-export everything from @testing-library/react
export * from '@testing-library/react'
export { customRender as render }

/**
 * Helper to create a mock user for testing
 */
export const createMockUser = (overrides?: Partial<import('../../stores/authStore').User>) => {
  return {
    id: 1,
    username: 'testuser',
    email: 'test@example.com',
    full_name: 'Test User',
    role: 'admin' as const,
    status: 'active' as const,
    is_active: true,
    created_at: '2024-01-01T00:00:00Z',
    last_login: '2024-01-01T00:00:00Z',
    ...overrides,
  }
}

/**
 * Helper to wait for async operations to complete
 */
export const waitForAsync = () => new Promise((resolve) => setTimeout(resolve, 0))

