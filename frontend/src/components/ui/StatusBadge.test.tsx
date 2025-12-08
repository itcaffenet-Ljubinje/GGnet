import { describe, it, expect } from 'vitest'
import { render, screen } from '../../__tests__/setup/test-utils'
import { StatusBadge } from './StatusBadge'

describe('StatusBadge', () => {
  describe('rendering', () => {
    it('should render badge with text', () => {
      render(<StatusBadge status="success" text="Active" />)
      
      expect(screen.getByText('Active')).toBeInTheDocument()
    })

    it('should render icon by default', () => {
      const { container } = render(<StatusBadge status="success" text="Active" />)
      
      // Check for icon (lucide-react icons render as SVG)
      const svg = container.querySelector('svg')
      expect(svg).toBeInTheDocument()
    })

    it('should not render icon when showIcon is false', () => {
      const { container } = render(
        <StatusBadge status="success" text="Active" showIcon={false} />
      )
      
      const svg = container.querySelector('svg')
      expect(svg).not.toBeInTheDocument()
    })
  })

  describe('status variants', () => {
    it('should apply success/active styling', () => {
      const { container } = render(<StatusBadge status="success" text="Success" />)
      const badge = container.firstChild as HTMLElement
      
      expect(badge).toHaveClass('text-green-600', 'bg-green-50')
    })

    it('should apply active styling', () => {
      const { container } = render(<StatusBadge status="active" text="Active" />)
      const badge = container.firstChild as HTMLElement
      
      expect(badge).toHaveClass('text-green-600', 'bg-green-50')
    })

    it('should apply warning styling', () => {
      const { container } = render(<StatusBadge status="warning" text="Warning" />)
      const badge = container.firstChild as HTMLElement
      
      expect(badge).toHaveClass('text-yellow-600', 'bg-yellow-50')
    })

    it('should apply error styling', () => {
      const { container } = render(<StatusBadge status="error" text="Error" />)
      const badge = container.firstChild as HTMLElement
      
      expect(badge).toHaveClass('text-red-600', 'bg-red-50')
    })

    it('should apply info styling', () => {
      const { container } = render(<StatusBadge status="info" text="Info" />)
      const badge = container.firstChild as HTMLElement
      
      expect(badge).toHaveClass('text-blue-600', 'bg-blue-50')
    })

    it('should apply inactive styling', () => {
      const { container } = render(<StatusBadge status="inactive" text="Inactive" />)
      const badge = container.firstChild as HTMLElement
      
      expect(badge).toHaveClass('text-gray-600', 'bg-gray-50')
    })

    it('should apply default styling for unknown status', () => {
      const { container } = render(<StatusBadge status="unknown" text="Unknown" />)
      const badge = container.firstChild as HTMLElement
      
      expect(badge).toHaveClass('text-gray-600', 'bg-gray-50')
    })
  })

  describe('custom className', () => {
    it('should apply custom className', () => {
      const { container } = render(
        <StatusBadge status="success" text="Test" className="custom-class" />
      )
      const badge = container.firstChild as HTMLElement
      
      expect(badge).toHaveClass('custom-class')
    })
  })

  describe('accessibility', () => {
    it('should be a span element', () => {
      const { container } = render(<StatusBadge status="success" text="Test" />)
      
      expect(container.firstChild?.nodeName).toBe('SPAN')
    })

    it('should have proper structure for screen readers', () => {
      render(<StatusBadge status="success" text="Active" />)
      
      expect(screen.getByText('Active')).toBeInTheDocument()
    })
  })
})

