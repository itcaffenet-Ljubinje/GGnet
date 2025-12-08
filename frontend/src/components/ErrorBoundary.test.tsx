import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen } from '../__tests__/setup/test-utils'
import userEvent from '@testing-library/user-event'
import { ErrorBoundary, ErrorFallback } from './ErrorBoundary'

// Component that throws an error
const ThrowError = ({ shouldThrow = false }: { shouldThrow?: boolean }) => {
  if (shouldThrow) {
    throw new Error('Test error')
  }
  return <div>No error</div>
}

// Suppress console.error for error boundary tests
const originalError = console.error
beforeEach(() => {
  console.error = vi.fn()
})

afterEach(() => {
  console.error = originalError
})

describe('ErrorBoundary', () => {
  describe('when no error occurs', () => {
    it('should render children normally', () => {
      render(
        <ErrorBoundary>
          <div>Test content</div>
        </ErrorBoundary>
      )

      expect(screen.getByText('Test content')).toBeInTheDocument()
    })
  })

  describe('when error occurs', () => {
    it('should catch error and display error UI', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      )

      expect(screen.getByText(/oops! something went wrong/i)).toBeInTheDocument()
      expect(screen.getByText(/we encountered an unexpected error/i)).toBeInTheDocument()
    })

    it('should display reload button', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      )

      const reloadButton = screen.getByRole('button', { name: /reload page/i })
      expect(reloadButton).toBeInTheDocument()
    })

    it('should display go home button', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      )

      const goHomeButton = screen.getByRole('button', { name: /go home/i })
      expect(goHomeButton).toBeInTheDocument()
    })

    it('should call window.location.reload when reload button is clicked', async () => {
      // Mock window.location.reload
      const originalReload = window.location.reload
      const mockReload = vi.fn()
      Object.defineProperty(window, 'location', {
        value: { ...window.location, reload: mockReload },
        writable: true,
      })

      const user = userEvent.setup()

      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      )

      const reloadButton = screen.getByRole('button', { name: /reload page/i })
      await user.click(reloadButton)

      expect(mockReload).toHaveBeenCalled()

      // Restore
      Object.defineProperty(window, 'location', {
        value: { ...window.location, reload: originalReload },
        writable: true,
      })
    })

    it('should navigate to dashboard when go home button is clicked', async () => {
      // Mock window.location.href
      const originalHref = window.location.href
      let hrefValue = originalHref
      Object.defineProperty(window, 'location', {
        value: {
          ...window.location,
          get href() {
            return hrefValue
          },
          set href(value: string) {
            hrefValue = value
          },
        },
        writable: true,
      })

      const user = userEvent.setup()

      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      )

      const goHomeButton = screen.getByRole('button', { name: /go home/i })
      await user.click(goHomeButton)

      expect(window.location.href).toBe('/dashboard')

      // Restore
      Object.defineProperty(window, 'location', {
        value: { ...window.location, href: originalHref },
        writable: true,
      })
    })

    it('should use custom fallback when provided', () => {
      const customFallback = <div>Custom error message</div>

      render(
        <ErrorBoundary fallback={customFallback}>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      )

      expect(screen.getByText('Custom error message')).toBeInTheDocument()
      expect(screen.queryByText(/oops! something went wrong/i)).not.toBeInTheDocument()
    })

    it('should log error to console', () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      )

      expect(consoleErrorSpy).toHaveBeenCalled()

      consoleErrorSpy.mockRestore()
    })
  })

  describe('getDerivedStateFromError', () => {
    it('should set hasError to true when error occurs', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      )

      // Error boundary should be showing error UI
      expect(screen.getByText(/oops! something went wrong/i)).toBeInTheDocument()
    })
  })
})

describe('ErrorFallback', () => {
  it('should render error message', () => {
    const error = new Error('Test error message')
    render(<ErrorFallback error={error} />)

    expect(screen.getByText('Test error message')).toBeInTheDocument()
  })

  it('should render default message when no error provided', () => {
    render(<ErrorFallback />)

    expect(screen.getByText(/an unexpected error occurred/i)).toBeInTheDocument()
  })

  it('should render try again button when resetError is provided', () => {
    const resetError = vi.fn()
    render(<ErrorFallback resetError={resetError} />)

    const tryAgainButton = screen.getByRole('button', { name: /try again/i })
    expect(tryAgainButton).toBeInTheDocument()
  })

  it('should not render try again button when resetError is not provided', () => {
    render(<ErrorFallback />)

    expect(screen.queryByRole('button', { name: /try again/i })).not.toBeInTheDocument()
  })

  it('should call resetError when try again button is clicked', async () => {
    const resetError = vi.fn()
    const user = userEvent.setup()

    render(<ErrorFallback resetError={resetError} />)

    const tryAgainButton = screen.getByRole('button', { name: /try again/i })
    await user.click(tryAgainButton)

    expect(resetError).toHaveBeenCalledTimes(1)
  })

  it('should display error icon', () => {
    render(<ErrorFallback />)

    // Check for AlertTriangle icon (lucide-react icons render as SVG)
    const svg = document.querySelector('svg')
    expect(svg).toBeInTheDocument()
  })
})

