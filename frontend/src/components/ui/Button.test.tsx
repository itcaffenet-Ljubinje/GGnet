import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '../../__tests__/setup/test-utils'
import userEvent from '@testing-library/user-event'
import { Button } from './Button'

describe('Button', () => {
  describe('rendering', () => {
    it('should render button with text', () => {
      render(<Button>Click me</Button>)
      
      expect(screen.getByRole('button', { name: /click me/i })).toBeInTheDocument()
    })

    it('should render button with custom className', () => {
      const { container } = render(<Button className="custom-class">Button</Button>)
      
      expect(container.firstChild).toHaveClass('custom-class')
    })

    it('should render disabled button', () => {
      render(<Button disabled>Disabled</Button>)
      
      expect(screen.getByRole('button')).toBeDisabled()
    })

    it('should render button with left icon', () => {
      const { container } = render(
        <Button leftIcon={<span data-testid="left-icon">←</span>}>Button</Button>
      )
      
      expect(screen.getByTestId('left-icon')).toBeInTheDocument()
    })

    it('should render button with right icon', () => {
      const { container } = render(
        <Button rightIcon={<span data-testid="right-icon">→</span>}>Button</Button>
      )
      
      expect(screen.getByTestId('right-icon')).toBeInTheDocument()
    })
  })

  describe('variants', () => {
    it('should apply primary variant styles', () => {
      const { container } = render(<Button variant="primary">Primary</Button>)
      const button = container.firstChild as HTMLElement
      
      expect(button).toHaveClass('bg-gradient-to-r', 'from-blue-600', 'to-blue-700')
    })

    it('should apply secondary variant styles', () => {
      const { container } = render(<Button variant="secondary">Secondary</Button>)
      const button = container.firstChild as HTMLElement
      
      expect(button).toHaveClass('bg-gradient-to-r', 'from-gray-100', 'to-gray-200')
    })

    it('should apply danger variant styles', () => {
      const { container } = render(<Button variant="danger">Danger</Button>)
      const button = container.firstChild as HTMLElement
      
      expect(button).toHaveClass('bg-gradient-to-r', 'from-red-600', 'to-red-700')
    })

    it('should apply ghost variant styles', () => {
      const { container } = render(<Button variant="ghost">Ghost</Button>)
      const button = container.firstChild as HTMLElement
      
      expect(button).toHaveClass('text-gray-600', 'hover:bg-gray-100/80')
    })

    it('should apply outline variant styles', () => {
      const { container } = render(<Button variant="outline">Outline</Button>)
      const button = container.firstChild as HTMLElement
      
      expect(button).toHaveClass('border', 'border-gray-300')
    })

    it('should default to primary variant', () => {
      const { container } = render(<Button>Default</Button>)
      const button = container.firstChild as HTMLElement
      
      expect(button).toHaveClass('bg-gradient-to-r', 'from-blue-600', 'to-blue-700')
    })
  })

  describe('sizes', () => {
    it('should apply small size styles', () => {
      const { container } = render(<Button size="sm">Small</Button>)
      const button = container.firstChild as HTMLElement
      
      expect(button).toHaveClass('px-3', 'py-1.5', 'text-sm')
    })

    it('should apply medium size styles', () => {
      const { container } = render(<Button size="md">Medium</Button>)
      const button = container.firstChild as HTMLElement
      
      expect(button).toHaveClass('px-4', 'py-2', 'text-sm')
    })

    it('should apply large size styles', () => {
      const { container } = render(<Button size="lg">Large</Button>)
      const button = container.firstChild as HTMLElement
      
      expect(button).toHaveClass('px-6', 'py-3', 'text-base')
    })

    it('should default to medium size', () => {
      const { container } = render(<Button>Default</Button>)
      const button = container.firstChild as HTMLElement
      
      expect(button).toHaveClass('px-4', 'py-2', 'text-sm')
    })
  })

  describe('loading state', () => {
    it('should show loading spinner when isLoading is true', () => {
      const { container } = render(<Button isLoading>Loading</Button>)
      
      const svg = container.querySelector('svg.animate-spin')
      expect(svg).toBeInTheDocument()
    })

    it('should disable button when loading', () => {
      render(<Button isLoading>Loading</Button>)
      
      expect(screen.getByRole('button')).toBeDisabled()
    })

    it('should not show icons when loading', () => {
      render(
        <Button 
          isLoading 
          leftIcon={<span data-testid="left">←</span>}
          rightIcon={<span data-testid="right">→</span>}
        >
          Loading
        </Button>
      )
      
      expect(screen.queryByTestId('left')).not.toBeInTheDocument()
      expect(screen.queryByTestId('right')).not.toBeInTheDocument()
    })
  })

  describe('user interactions', () => {
    it('should call onClick when clicked', async () => {
      const handleClick = vi.fn()
      const user = userEvent.setup()
      
      render(<Button onClick={handleClick}>Click me</Button>)
      
      await user.click(screen.getByRole('button'))
      
      expect(handleClick).toHaveBeenCalledTimes(1)
    })

    it('should not call onClick when disabled', async () => {
      const handleClick = vi.fn()
      const user = userEvent.setup()
      
      render(<Button onClick={handleClick} disabled>Disabled</Button>)
      
      await user.click(screen.getByRole('button'))
      
      expect(handleClick).not.toHaveBeenCalled()
    })

    it('should not call onClick when loading', async () => {
      const handleClick = vi.fn()
      const user = userEvent.setup()
      
      render(<Button onClick={handleClick} isLoading>Loading</Button>)
      
      const button = screen.getByRole('button')
      await user.click(button)
      
      expect(handleClick).not.toHaveBeenCalled()
    })
  })

  describe('accessibility', () => {
    it('should have proper button role', () => {
      render(<Button>Button</Button>)
      
      expect(screen.getByRole('button')).toBeInTheDocument()
    })

    it('should support aria-label', () => {
      render(<Button aria-label="Close dialog">×</Button>)
      
      expect(screen.getByRole('button')).toHaveAttribute('aria-label', 'Close dialog')
    })

    it('should support aria-disabled', () => {
      render(<Button disabled aria-disabled="true">Disabled</Button>)
      
      expect(screen.getByRole('button')).toHaveAttribute('aria-disabled', 'true')
    })
  })

  describe('ref forwarding', () => {
    it('should forward ref to button element', () => {
      const ref = vi.fn()
      
      render(<Button ref={ref}>Button</Button>)
      
      expect(ref).toHaveBeenCalled()
    })
  })
})

