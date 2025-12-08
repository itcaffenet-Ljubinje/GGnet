// Vitest globals are available via globals: true in vitest.config.ts
import { render } from '../../__tests__/setup/test-utils'
import userEvent from '@testing-library/user-event'
import { Input } from './Input'

describe('Input', () => {
  describe('rendering', () => {
    it('should render input element', () => {
      render(<Input />)
      
      expect(screen.getByRole('textbox')).toBeInTheDocument()
    })

    it('should render input with label', () => {
      render(<Input label="Username" />)
      
      expect(screen.getByLabelText('Username')).toBeInTheDocument()
    })

    it('should render input with placeholder', () => {
      render(<Input placeholder="Enter text" />)
      
      expect(screen.getByPlaceholderText('Enter text')).toBeInTheDocument()
    })

    it('should render input with value', () => {
      render(<Input value="test value" onChange={() => {}} />)
      
      expect(screen.getByDisplayValue('test value')).toBeInTheDocument()
    })
  })

  describe('error state', () => {
    it('should display error message', () => {
      render(<Input error="This field is required" />)
      
      expect(screen.getByText('This field is required')).toBeInTheDocument()
      expect(screen.getByText('This field is required')).toHaveClass('text-red-600')
    })

    it('should apply error styling to input', () => {
      const { container } = render(<Input error="Error message" />)
      const input = container.querySelector('input')
      
      expect(input).toHaveClass('border-red-300', 'focus:border-red-500', 'focus:ring-red-500')
    })

    it('should not show helper text when error is present', () => {
      render(<Input error="Error" helperText="Helper text" />)
      
      expect(screen.queryByText('Helper text')).not.toBeInTheDocument()
      expect(screen.getByText('Error')).toBeInTheDocument()
    })
  })

  describe('helper text', () => {
    it('should display helper text when no error', () => {
      render(<Input helperText="This is helpful information" />)
      
      expect(screen.getByText('This is helpful information')).toBeInTheDocument()
      expect(screen.getByText('This is helpful information')).toHaveClass('text-gray-500')
    })
  })

  describe('icons', () => {
    it('should render left icon', () => {
      render(<Input leftIcon={<span data-testid="left-icon">@</span>} />)
      
      expect(screen.getByTestId('left-icon')).toBeInTheDocument()
    })

    it('should render right icon', () => {
      render(<Input rightIcon={<span data-testid="right-icon">✓</span>} />)
      
      expect(screen.getByTestId('right-icon')).toBeInTheDocument()
    })

    it('should apply padding when icons are present', () => {
      const { container } = render(<Input leftIcon={<span>@</span>} />)
      const input = container.querySelector('input')
      
      expect(input).toHaveClass('pl-10')
    })
  })

  describe('variants', () => {
    it('should apply default variant styles', () => {
      const { container } = render(<Input variant="default" />)
      const input = container.querySelector('input')
      
      expect(input).toHaveClass('border-gray-300', 'bg-white')
    })

    it('should apply filled variant styles', () => {
      const { container } = render(<Input variant="filled" />)
      const input = container.querySelector('input')
      
      expect(input).toHaveClass('bg-gray-100', 'border-transparent')
    })

    it('should default to default variant', () => {
      const { container } = render(<Input />)
      const input = container.querySelector('input')
      
      expect(input).toHaveClass('border-gray-300', 'bg-white')
    })
  })

  describe('user interactions', () => {
    it('should handle input changes', async () => {
      const handleChange = vi.fn()
      const user = userEvent.setup()
      
      render(<Input onChange={handleChange} />)
      
      const input = screen.getByRole('textbox')
      await user.type(input, 'test')
      
      expect(handleChange).toHaveBeenCalled()
    })

    it('should handle focus events', async () => {
      const handleFocus = vi.fn()
      const user = userEvent.setup()
      
      render(<Input onFocus={handleFocus} />)
      
      const input = screen.getByRole('textbox')
      await user.click(input)
      
      expect(handleFocus).toHaveBeenCalled()
    })

    it('should handle blur events', async () => {
      const handleBlur = vi.fn()
      const user = userEvent.setup()
      
      render(<Input onBlur={handleBlur} />)
      
      const input = screen.getByRole('textbox')
      await user.click(input)
      await user.tab()
      
      expect(handleBlur).toHaveBeenCalled()
    })
  })

  describe('input types', () => {
    it('should support text type', () => {
      render(<Input type="text" />)
      
      expect(screen.getByRole('textbox')).toHaveAttribute('type', 'text')
    })

    it('should support password type', () => {
      const { container } = render(<Input type="password" />)
      const input = container.querySelector('input[type="password"]')
      
      expect(input).toBeInTheDocument()
      expect(input).toHaveAttribute('type', 'password')
    })

    it('should support email type', () => {
      render(<Input type="email" label="Email" />)
      
      expect(screen.getByLabelText('Email')).toHaveAttribute('type', 'email')
    })

    it('should support number type', () => {
      render(<Input type="number" />)
      
      const input = screen.getByRole('spinbutton')
      expect(input).toHaveAttribute('type', 'number')
    })
  })

  describe('disabled state', () => {
    it('should render disabled input', () => {
      render(<Input disabled />)
      
      expect(screen.getByRole('textbox')).toBeDisabled()
    })
  })

  describe('accessibility', () => {
    it('should associate label with input', () => {
      render(<Input label="Username" id="username" />)
      
      const input = screen.getByLabelText('Username')
      expect(input).toHaveAttribute('id', 'username')
    })

    it('should generate unique id when not provided', () => {
      const { container } = render(<Input label="Test" />)
      const input = container.querySelector('input')
      const label = container.querySelector('label')
      
      expect(input).toHaveAttribute('id')
      expect(label).toHaveAttribute('for', input?.getAttribute('id'))
    })

    it('should display error message for accessibility', () => {
      render(<Input error="Error message" id="test-input" />)
      
      const input = screen.getByRole('textbox')
      const errorMessage = screen.getByText('Error message')
      
      expect(input).toBeInTheDocument()
      expect(errorMessage).toBeInTheDocument()
      expect(errorMessage).toHaveClass('text-red-600')
    })
  })

  describe('ref forwarding', () => {
    it('should forward ref to input element', () => {
      const ref = vi.fn()
      
      render(<Input ref={ref} />)
      
      expect(ref).toHaveBeenCalled()
    })
  })
})

