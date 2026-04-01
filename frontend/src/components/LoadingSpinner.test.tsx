// Vitest globals are available via globals: true in vitest.config.ts
import { render, screen } from '../__tests__/setup/test-utils'
import { LoadingSpinner, LoadingOverlay, LoadingPage } from './LoadingSpinner'

describe('LoadingSpinner', () => {
  describe('rendering', () => {
    it('should render spinner with default size', () => {
      const { container } = render(<LoadingSpinner />)
      
      const svg = container.querySelector('svg')
      expect(svg).toBeInTheDocument()
      expect(svg).toHaveClass('h-8', 'w-8') // default md size
    })

    it('should render spinner with small size', () => {
      const { container } = render(<LoadingSpinner size="sm" />)
      
      const svg = container.querySelector('svg')
      expect(svg).toHaveClass('h-4', 'w-4')
    })

    it('should render spinner with medium size', () => {
      const { container } = render(<LoadingSpinner size="md" />)
      
      const svg = container.querySelector('svg')
      expect(svg).toHaveClass('h-8', 'w-8')
    })

    it('should render spinner with large size', () => {
      const { container } = render(<LoadingSpinner size="lg" />)
      
      const svg = container.querySelector('svg')
      expect(svg).toHaveClass('h-12', 'w-12')
    })

    it('should render with custom className', () => {
      const { container } = render(<LoadingSpinner className="custom-class" />)
      
      const wrapper = container.firstChild as HTMLElement
      expect(wrapper).toHaveClass('custom-class')
    })

    it('should render text when provided', () => {
      render(<LoadingSpinner text="Loading data..." />)
      
      expect(screen.getByText('Loading data...')).toBeInTheDocument()
    })

    it('should not render text when not provided', () => {
      const { container } = render(<LoadingSpinner />)
      
      const textElement = container.querySelector('p')
      expect(textElement).not.toBeInTheDocument()
    })
  })

  describe('spinner structure', () => {
    it('should have animate-spin class', () => {
      const { container } = render(<LoadingSpinner />)
      
      const svg = container.querySelector('svg')
      expect(svg).toHaveClass('animate-spin')
    })

    it('should have proper SVG structure', () => {
      const { container } = render(<LoadingSpinner />)
      
      const circle = container.querySelector('circle')
      const path = container.querySelector('path')
      
      expect(circle).toBeInTheDocument()
      expect(path).toBeInTheDocument()
    })
  })
})

describe('LoadingOverlay', () => {
  describe('when loading', () => {
    it('should show overlay and spinner', () => {
      render(
        <LoadingOverlay isLoading={true}>
          <div>Content</div>
        </LoadingOverlay>
      )
      
      expect(screen.getByText('Loading...')).toBeInTheDocument()
    })

    it('should show custom loading text', () => {
      render(
        <LoadingOverlay isLoading={true} text="Please wait...">
          <div>Content</div>
        </LoadingOverlay>
      )
      
      expect(screen.getByText('Please wait...')).toBeInTheDocument()
    })

    it('should render children behind overlay', () => {
      render(
        <LoadingOverlay isLoading={true}>
          <div>Content</div>
        </LoadingOverlay>
      )
      
      expect(screen.getByText('Content')).toBeInTheDocument()
    })

    it('should have overlay with proper classes', () => {
      const { container } = render(
        <LoadingOverlay isLoading={true}>
          <div>Content</div>
        </LoadingOverlay>
      )
      
      const overlay = container.querySelector('.absolute.inset-0')
      expect(overlay).toBeInTheDocument()
    })
  })

  describe('when not loading', () => {
    it('should render children without overlay', () => {
      render(
        <LoadingOverlay isLoading={false}>
          <div>Content</div>
        </LoadingOverlay>
      )
      
      expect(screen.getByText('Content')).toBeInTheDocument()
      expect(screen.queryByText('Loading...')).not.toBeInTheDocument()
    })
  })
})

describe('LoadingPage', () => {
  it('should render full page loading spinner', () => {
    render(<LoadingPage />)
    
    expect(screen.getByText('Loading...')).toBeInTheDocument()
  })

  it('should render with custom text', () => {
    render(<LoadingPage text="Initializing..." />)
    
    expect(screen.getByText('Initializing...')).toBeInTheDocument()
  })

  it('should have proper page layout classes', () => {
    const { container } = render(<LoadingPage />)
    
    const page = container.firstChild as HTMLElement
    expect(page).toHaveClass('min-h-screen', 'flex', 'items-center', 'justify-center')
  })

  it('should use large spinner size', () => {
    const { container } = render(<LoadingPage />)
    
    const svg = container.querySelector('svg')
    expect(svg).toHaveClass('h-12', 'w-12')
  })
})

