// Vitest globals are available via globals: true in vitest.config.ts
import { render, screen } from '../__tests__/setup/test-utils'
import userEvent from '@testing-library/user-event'
import NotFoundPage from './NotFoundPage'

describe('NotFoundPage', () => {
  it('should render 404 heading', () => {
    render(<NotFoundPage />)
    
    expect(screen.getByRole('heading', { name: /404/i })).toBeInTheDocument()
  })

  it('should render page not found message', () => {
    render(<NotFoundPage />)
    
    expect(screen.getByText(/page not found/i)).toBeInTheDocument()
    expect(screen.getByText(/doesn't exist or has been moved/i)).toBeInTheDocument()
  })

  it('should render dashboard link', () => {
    render(<NotFoundPage />)
    
    const dashboardLink = screen.getByRole('link', { name: /go to dashboard/i })
    expect(dashboardLink).toBeInTheDocument()
    expect(dashboardLink).toHaveAttribute('href', '/dashboard')
  })

  it('should render go back button', () => {
    render(<NotFoundPage />)
    
    const goBackButton = screen.getByRole('button', { name: /go back/i })
    expect(goBackButton).toBeInTheDocument()
  })

  it('should call window.history.back when go back button is clicked', async () => {
    const mockBack = vi.fn()
    window.history.back = mockBack
    
    const user = userEvent.setup()
    render(<NotFoundPage />)
    
    const goBackButton = screen.getByRole('button', { name: /go back/i })
    await user.click(goBackButton)
    
    expect(mockBack).toHaveBeenCalledTimes(1)
  })

  it('should render GG logo', () => {
    render(<NotFoundPage />)
    
    const logo = screen.getByText('GG')
    expect(logo).toBeInTheDocument()
  })

  it('should have proper structure and styling classes', () => {
    const { container } = render(<NotFoundPage />)
    
    // Check main container
    const mainContainer = container.firstChild
    expect(mainContainer).toHaveClass('min-h-screen', 'bg-gray-50', 'flex', 'flex-col')
  })
})

