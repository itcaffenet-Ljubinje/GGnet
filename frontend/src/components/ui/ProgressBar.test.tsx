// Vitest globals are available via globals: true in vitest.config.ts
import { render, screen } from '../../__tests__/setup/test-utils'
import { ProgressBar } from './ProgressBar'

describe('ProgressBar', () => {
  describe('rendering', () => {
    it('should render progress bar', () => {
      const { container } = render(<ProgressBar value={50} />)
      
      const progressBar = container.querySelector('.w-full.bg-gray-200')
      expect(progressBar).toBeInTheDocument()
    })

    it('should calculate percentage correctly', () => {
      const { container } = render(<ProgressBar value={50} max={100} />)
      
      const fill = container.querySelector('.bg-blue-600') as HTMLElement
      expect(fill).toHaveStyle({ width: '50%' })
    })

    it('should use progress prop when provided', () => {
      const { container } = render(<ProgressBar progress={75} />)
      
      const fill = container.querySelector('.bg-blue-600') as HTMLElement
      expect(fill).toHaveStyle({ width: '75%' })
    })

    it('should prefer progress over value', () => {
      const { container } = render(<ProgressBar value={50} progress={80} />)
      
      const fill = container.querySelector('.bg-blue-600') as HTMLElement
      expect(fill).toHaveStyle({ width: '80%' })
    })

    it('should default to 0 when no value provided', () => {
      const { container } = render(<ProgressBar />)
      
      const fill = container.querySelector('.bg-blue-600') as HTMLElement
      expect(fill).toHaveStyle({ width: '0%' })
    })

    it('should cap at 100%', () => {
      const { container } = render(<ProgressBar value={150} max={100} />)
      
      const fill = container.querySelector('.bg-blue-600') as HTMLElement
      expect(fill).toHaveStyle({ width: '100%' })
    })
  })

  describe('max value', () => {
    it('should use custom max value', () => {
      const { container } = render(<ProgressBar value={50} max={200} />)
      
      const fill = container.querySelector('.bg-blue-600') as HTMLElement
      expect(fill).toHaveStyle({ width: '25%' })
    })

    it('should default to 100', () => {
      const { container } = render(<ProgressBar value={50} />)
      
      const fill = container.querySelector('.bg-blue-600') as HTMLElement
      expect(fill).toHaveStyle({ width: '50%' })
    })
  })

  describe('colors', () => {
    it('should apply blue color by default', () => {
      const { container } = render(<ProgressBar value={50} />)
      
      const fill = container.querySelector('.bg-blue-600')
      expect(fill).toBeInTheDocument()
    })

    it('should apply green color', () => {
      const { container } = render(<ProgressBar value={50} color="green" />)
      
      const fill = container.querySelector('.bg-green-600')
      expect(fill).toBeInTheDocument()
    })

    it('should apply yellow color', () => {
      const { container } = render(<ProgressBar value={50} color="yellow" />)
      
      const fill = container.querySelector('.bg-yellow-600')
      expect(fill).toBeInTheDocument()
    })

    it('should apply red color', () => {
      const { container } = render(<ProgressBar value={50} color="red" />)
      
      const fill = container.querySelector('.bg-red-600')
      expect(fill).toBeInTheDocument()
    })

    it('should apply gray color', () => {
      const { container } = render(<ProgressBar value={50} color="gray" />)
      
      const fill = container.querySelector('.bg-gray-600')
      expect(fill).toBeInTheDocument()
    })
  })

  describe('sizes', () => {
    it('should apply small size', () => {
      const { container } = render(<ProgressBar value={50} size="sm" />)
      
      const fill = container.querySelector('.h-2')
      expect(fill).toBeInTheDocument()
    })

    it('should apply medium size by default', () => {
      const { container } = render(<ProgressBar value={50} />)
      
      const fill = container.querySelector('.h-3')
      expect(fill).toBeInTheDocument()
    })

    it('should apply large size', () => {
      const { container } = render(<ProgressBar value={50} size="lg" />)
      
      const fill = container.querySelector('.h-4')
      expect(fill).toBeInTheDocument()
    })
  })

  describe('labels', () => {
    it('should not show label by default', () => {
      render(<ProgressBar value={50} />)
      
      expect(screen.queryByText('Progress')).not.toBeInTheDocument()
    })

    it('should show label when showLabel is true', () => {
      render(<ProgressBar value={50} showLabel />)
      
      expect(screen.getByText('Progress')).toBeInTheDocument()
      expect(screen.getByText('50%')).toBeInTheDocument()
    })

    it('should show custom label', () => {
      render(<ProgressBar value={50} showLabel label="Upload Progress" />)
      
      expect(screen.getByText('Upload Progress')).toBeInTheDocument()
      expect(screen.getByText('50%')).toBeInTheDocument()
    })

    it('should round percentage in label', () => {
      render(<ProgressBar value={33.7} showLabel />)
      
      expect(screen.getByText('34%')).toBeInTheDocument()
    })
  })

  describe('custom className', () => {
    it('should apply custom className', () => {
      const { container } = render(<ProgressBar value={50} className="custom-class" />)
      
      const wrapper = container.firstChild as HTMLElement
      expect(wrapper).toHaveClass('custom-class')
    })
  })
})

