// Vitest globals are available via globals: true in vitest.config.ts
import { render, screen } from '../../__tests__/setup/test-utils'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from './Card'

describe('Card', () => {
  describe('rendering', () => {
    it('should render card with children', () => {
      render(<Card>Card content</Card>)
      
      expect(screen.getByText('Card content')).toBeInTheDocument()
    })

    it('should apply default variant styles', () => {
      const { container } = render(<Card>Content</Card>)
      const card = container.firstChild as HTMLElement
      
      expect(card).toHaveClass('bg-white/90', 'border', 'border-gray-200/50')
    })

    it('should apply default padding', () => {
      const { container } = render(<Card>Content</Card>)
      const card = container.firstChild as HTMLElement
      
      expect(card).toHaveClass('p-6') // default md padding
    })
  })

  describe('variants', () => {
    it('should apply default variant', () => {
      const { container } = render(<Card variant="default">Content</Card>)
      const card = container.firstChild as HTMLElement
      
      expect(card).toHaveClass('bg-white/90', 'border', 'border-gray-200/50')
    })

    it('should apply elevated variant', () => {
      const { container } = render(<Card variant="elevated">Content</Card>)
      const card = container.firstChild as HTMLElement
      
      expect(card).toHaveClass('bg-white/95', 'shadow-xl')
    })

    it('should apply outlined variant', () => {
      const { container } = render(<Card variant="outlined">Content</Card>)
      const card = container.firstChild as HTMLElement
      
      expect(card).toHaveClass('bg-white/80', 'border-2', 'border-gray-200/60')
    })
  })

  describe('padding', () => {
    it('should apply no padding', () => {
      const { container } = render(<Card padding="none">Content</Card>)
      const card = container.firstChild as HTMLElement
      
      expect(card).not.toHaveClass('p-4', 'p-6', 'p-8')
    })

    it('should apply small padding', () => {
      const { container } = render(<Card padding="sm">Content</Card>)
      const card = container.firstChild as HTMLElement
      
      expect(card).toHaveClass('p-4')
    })

    it('should apply medium padding', () => {
      const { container } = render(<Card padding="md">Content</Card>)
      const card = container.firstChild as HTMLElement
      
      expect(card).toHaveClass('p-6')
    })

    it('should apply large padding', () => {
      const { container } = render(<Card padding="lg">Content</Card>)
      const card = container.firstChild as HTMLElement
      
      expect(card).toHaveClass('p-8')
    })
  })

  describe('custom className', () => {
    it('should apply custom className', () => {
      const { container } = render(<Card className="custom-class">Content</Card>)
      const card = container.firstChild as HTMLElement
      
      expect(card).toHaveClass('custom-class')
    })
  })

  describe('ref forwarding', () => {
    it('should forward ref to card element', () => {
      const ref = vi.fn()
      
      render(<Card ref={ref}>Content</Card>)
      
      expect(ref).toHaveBeenCalled()
    })
  })
})

describe('CardHeader', () => {
  it('should render header with children', () => {
    render(<CardHeader>Header content</CardHeader>)
    
    expect(screen.getByText('Header content')).toBeInTheDocument()
  })

  it('should apply default styles', () => {
    const { container } = render(<CardHeader>Header</CardHeader>)
    const header = container.firstChild as HTMLElement
    
    expect(header).toHaveClass('mb-4')
  })

  it('should forward ref', () => {
    const ref = vi.fn()
    
    render(<CardHeader ref={ref}>Header</CardHeader>)
    
    expect(ref).toHaveBeenCalled()
  })
})

describe('CardTitle', () => {
  it('should render title with children', () => {
    render(<CardTitle>Card Title</CardTitle>)
    
    expect(screen.getByText('Card Title')).toBeInTheDocument()
  })

  it('should render as h3 element', () => {
    const { container } = render(<CardTitle>Title</CardTitle>)
    
    expect(container.querySelector('h3')).toBeInTheDocument()
  })

  it('should apply default styles', () => {
    const { container } = render(<CardTitle>Title</CardTitle>)
    const title = container.querySelector('h3')
    
    expect(title).toHaveClass('text-lg', 'font-semibold')
  })

  it('should forward ref', () => {
    const ref = vi.fn()
    
    render(<CardTitle ref={ref}>Title</CardTitle>)
    
    expect(ref).toHaveBeenCalled()
  })
})

describe('CardDescription', () => {
  it('should render description with children', () => {
    render(<CardDescription>Description text</CardDescription>)
    
    expect(screen.getByText('Description text')).toBeInTheDocument()
  })

  it('should render as p element', () => {
    const { container } = render(<CardDescription>Description</CardDescription>)
    
    expect(container.querySelector('p')).toBeInTheDocument()
  })

  it('should apply default styles', () => {
    const { container } = render(<CardDescription>Description</CardDescription>)
    const desc = container.querySelector('p')
    
    expect(desc).toHaveClass('text-sm', 'text-gray-600', 'mt-1')
  })

  it('should forward ref', () => {
    const ref = vi.fn()
    
    render(<CardDescription ref={ref}>Description</CardDescription>)
    
    expect(ref).toHaveBeenCalled()
  })
})

describe('CardContent', () => {
  it('should render content with children', () => {
    render(<CardContent>Content text</CardContent>)
    
    expect(screen.getByText('Content text')).toBeInTheDocument()
  })

  it('should render as div element', () => {
    const { container } = render(<CardContent>Content</CardContent>)
    
    expect(container.querySelector('div')).toBeInTheDocument()
  })

  it('should forward ref', () => {
    const ref = vi.fn()
    
    render(<CardContent ref={ref}>Content</CardContent>)
    
    expect(ref).toHaveBeenCalled()
  })
})

describe('CardFooter', () => {
  it('should render footer with children', () => {
    render(<CardFooter>Footer content</CardFooter>)
    
    expect(screen.getByText('Footer content')).toBeInTheDocument()
  })

  it('should apply default styles', () => {
    const { container } = render(<CardFooter>Footer</CardFooter>)
    const footer = container.firstChild as HTMLElement
    
    expect(footer).toHaveClass('mt-4', 'pt-4', 'border-t')
  })

  it('should forward ref', () => {
    const ref = vi.fn()
    
    render(<CardFooter ref={ref}>Footer</CardFooter>)
    
    expect(ref).toHaveBeenCalled()
  })
})

describe('Card composition', () => {
  it('should work with all subcomponents together', () => {
    render(
      <Card>
        <CardHeader>
          <CardTitle>Test Title</CardTitle>
          <CardDescription>Test Description</CardDescription>
        </CardHeader>
        <CardContent>Test Content</CardContent>
        <CardFooter>Test Footer</CardFooter>
      </Card>
    )
    
    expect(screen.getByText('Test Title')).toBeInTheDocument()
    expect(screen.getByText('Test Description')).toBeInTheDocument()
    expect(screen.getByText('Test Content')).toBeInTheDocument()
    expect(screen.getByText('Test Footer')).toBeInTheDocument()
  })
})

