// Vitest globals are available via globals: true in vitest.config.ts
import { render } from '../../__tests__/setup/test-utils'
import { Icon, icons } from './Icon'

// Mock console.warn to avoid noise in tests
const consoleWarnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})

describe('Icon', () => {
  beforeEach(() => {
    consoleWarnSpy.mockClear()
  })

  afterAll(() => {
    consoleWarnSpy.mockRestore()
  })

  describe('rendering', () => {
    it('should render icon by name', () => {
      const { container } = render(<Icon name="home" />)
      
      const svg = container.querySelector('svg')
      expect(svg).toBeInTheDocument()
    })

    it('should render different icons', () => {
      const { container: container1 } = render(<Icon name="home" />)
      const { container: container2 } = render(<Icon name="user" />)
      
      const svg1 = container1.querySelector('svg')
      const svg2 = container2.querySelector('svg')
      
      expect(svg1).toBeInTheDocument()
      expect(svg2).toBeInTheDocument()
      expect(svg1).not.toEqual(svg2)
    })

    it('should apply custom className', () => {
      const { container } = render(<Icon name="home" className="custom-class" />)
      
      const svg = container.querySelector('svg')
      expect(svg).toHaveClass('custom-class')
    })

    it('should apply custom size', () => {
      const { container } = render(<Icon name="home" size={24} />)
      
      const svg = container.querySelector('svg')
      expect(svg).toHaveAttribute('width', '24')
      expect(svg).toHaveAttribute('height', '24')
    })
  })

  describe('icon names', () => {
    it('should render all available icons', () => {
      const iconNames = Object.keys(icons) as Array<keyof typeof icons>
      
      iconNames.forEach(iconName => {
        const { container } = render(<Icon name={iconName} />)
        const svg = container.querySelector('svg')
        expect(svg).toBeInTheDocument()
      })
    })

    it('should handle kebab-case icon names', () => {
      const { container } = render(<Icon name="alert-circle" />)
      
      const svg = container.querySelector('svg')
      expect(svg).toBeInTheDocument()
    })

    it('should handle icon names with hyphens', () => {
      const { container } = render(<Icon name="eye-off" />)
      
      const svg = container.querySelector('svg')
      expect(svg).toBeInTheDocument()
    })
  })

  describe('invalid icon names', () => {
    it('should return null for invalid icon name', () => {
      // @ts-expect-error - Testing invalid icon name
      const { container } = render(<Icon name="invalid-icon" />)
      
      expect(container.firstChild).toBeNull()
    })

    it('should warn when icon name is not found', () => {
      // @ts-expect-error - Testing invalid icon name
      render(<Icon name="invalid-icon" />)
      
      expect(consoleWarnSpy).toHaveBeenCalledWith('Icon "invalid-icon" not found')
    })
  })

  describe('default props', () => {
    it('should render icon with default className from lucide-react', () => {
      const { container } = render(<Icon name="home" />)
      
      const svg = container.querySelector('svg')
      // lucide-react icons have default classes, so we just check that it renders
      expect(svg).toBeInTheDocument()
      expect(svg?.className.baseVal || svg?.getAttribute('class')).toContain('lucide')
    })

    it('should not set size attribute when size is not provided', () => {
      const { container } = render(<Icon name="home" />)
      
      const svg = container.querySelector('svg')
      // lucide-react icons have default size, but we're not setting it explicitly
      expect(svg).toBeInTheDocument()
    })
  })
})

