// Vitest globals are available via globals: true in vitest.config.ts
import { render, screen, waitFor } from '../../__tests__/setup/test-utils'
import userEvent from '@testing-library/user-event'
import { Modal, ConfirmModal } from './Modal'

describe('Modal', () => {
  const mockOnClose = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    document.body.style.overflow = ''
  })

  describe('rendering', () => {
    it('should not render when isOpen is false', () => {
      render(
        <Modal isOpen={false} onClose={mockOnClose}>
          <div>Modal content</div>
        </Modal>
      )
      
      expect(screen.queryByText('Modal content')).not.toBeInTheDocument()
    })

    it('should render when isOpen is true', () => {
      render(
        <Modal isOpen={true} onClose={mockOnClose}>
          <div>Modal content</div>
        </Modal>
      )
      
      expect(screen.getByText('Modal content')).toBeInTheDocument()
    })

    it('should render title when provided', () => {
      render(
        <Modal isOpen={true} onClose={mockOnClose} title="Test Modal">
          <div>Content</div>
        </Modal>
      )
      
      expect(screen.getByText('Test Modal')).toBeInTheDocument()
    })

    it('should not render header when title and showCloseButton are false', () => {
      render(
        <Modal isOpen={true} onClose={mockOnClose} showCloseButton={false}>
          <div>Content</div>
        </Modal>
      )
      
      const header = screen.queryByRole('heading')
      expect(header).not.toBeInTheDocument()
    })
  })

  describe('sizes', () => {
    it('should apply small size', () => {
      const { container } = render(
        <Modal isOpen={true} onClose={mockOnClose} size="sm">
          <div>Content</div>
        </Modal>
      )
      
      const modal = container.querySelector('.max-w-md')
      expect(modal).toBeInTheDocument()
    })

    it('should apply medium size by default', () => {
      const { container } = render(
        <Modal isOpen={true} onClose={mockOnClose}>
          <div>Content</div>
        </Modal>
      )
      
      const modal = container.querySelector('.max-w-lg')
      expect(modal).toBeInTheDocument()
    })

    it('should apply large size', () => {
      const { container } = render(
        <Modal isOpen={true} onClose={mockOnClose} size="lg">
          <div>Content</div>
        </Modal>
      )
      
      const modal = container.querySelector('.max-w-2xl')
      expect(modal).toBeInTheDocument()
    })

    it('should apply xl size', () => {
      const { container } = render(
        <Modal isOpen={true} onClose={mockOnClose} size="xl">
          <div>Content</div>
        </Modal>
      )
      
      const modal = container.querySelector('.max-w-4xl')
      expect(modal).toBeInTheDocument()
    })

    it('should apply full size', () => {
      const { container } = render(
        <Modal isOpen={true} onClose={mockOnClose} size="full">
          <div>Content</div>
        </Modal>
      )
      
      const modal = container.querySelector('.max-w-full')
      expect(modal).toBeInTheDocument()
    })
  })

  describe('close button', () => {
    it('should show close button by default', () => {
      render(
        <Modal isOpen={true} onClose={mockOnClose}>
          <div>Content</div>
        </Modal>
      )
      
      const closeButton = screen.getByRole('button')
      expect(closeButton).toBeInTheDocument()
    })

    it('should hide close button when showCloseButton is false', () => {
      render(
        <Modal isOpen={true} onClose={mockOnClose} showCloseButton={false}>
          <div>Content</div>
        </Modal>
      )
      
      const closeButtons = screen.queryAllByRole('button')
      expect(closeButtons.length).toBe(0)
    })

    it('should call onClose when close button is clicked', async () => {
      const user = userEvent.setup()
      render(
        <Modal isOpen={true} onClose={mockOnClose}>
          <div>Content</div>
        </Modal>
      )
      
      const closeButton = screen.getByRole('button')
      await user.click(closeButton)
      
      expect(mockOnClose).toHaveBeenCalledTimes(1)
    })
  })

  describe('backdrop', () => {
    it('should render backdrop', () => {
      const { container } = render(
        <Modal isOpen={true} onClose={mockOnClose}>
          <div>Content</div>
        </Modal>
      )
      
      const backdrop = container.querySelector('.fixed.inset-0.bg-black')
      expect(backdrop).toBeInTheDocument()
    })

    it('should call onClose when backdrop is clicked', async () => {
      const user = userEvent.setup()
      const { container } = render(
        <Modal isOpen={true} onClose={mockOnClose}>
          <div>Content</div>
        </Modal>
      )
      
      const backdrop = container.querySelector('.fixed.inset-0.bg-black') as HTMLElement
      await user.click(backdrop)
      
      expect(mockOnClose).toHaveBeenCalledTimes(1)
    })
  })

  describe('keyboard events', () => {
    it('should call onClose when Escape key is pressed', async () => {
      render(
        <Modal isOpen={true} onClose={mockOnClose}>
          <div>Content</div>
        </Modal>
      )
      
      await userEvent.keyboard('{Escape}')
      
      await waitFor(() => {
        expect(mockOnClose).toHaveBeenCalledTimes(1)
      })
    })
  })

  describe('body overflow', () => {
    it('should set body overflow to hidden when modal opens', () => {
      render(
        <Modal isOpen={true} onClose={mockOnClose}>
          <div>Content</div>
        </Modal>
      )
      
      expect(document.body.style.overflow).toBe('hidden')
    })

    it('should restore body overflow when modal closes', () => {
      const { rerender } = render(
        <Modal isOpen={true} onClose={mockOnClose}>
          <div>Content</div>
        </Modal>
      )
      
      expect(document.body.style.overflow).toBe('hidden')
      
      rerender(
        <Modal isOpen={false} onClose={mockOnClose}>
          <div>Content</div>
        </Modal>
      )
      
      expect(document.body.style.overflow).toBe('unset')
    })
  })
})

describe('ConfirmModal', () => {
  const mockOnClose = vi.fn()
  const mockOnConfirm = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('rendering', () => {
    it('should render with title and message', () => {
      render(
        <ConfirmModal
          isOpen={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
          title="Confirm Action"
          message="Are you sure?"
        />
      )
      
      expect(screen.getByText('Confirm Action')).toBeInTheDocument()
      expect(screen.getByText('Are you sure?')).toBeInTheDocument()
    })

    it('should render with default button texts', () => {
      render(
        <ConfirmModal
          isOpen={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
          title="Confirm Action"
          message="Message"
        />
      )
      
      expect(screen.getByText('Confirm Action')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Confirm' })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Cancel' })).toBeInTheDocument()
    })

    it('should render with custom button texts', () => {
      render(
        <ConfirmModal
          isOpen={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
          title="Confirm"
          message="Message"
          confirmText="Yes, delete"
          cancelText="No, keep"
        />
      )
      
      expect(screen.getByText('Yes, delete')).toBeInTheDocument()
      expect(screen.getByText('No, keep')).toBeInTheDocument()
    })
  })

  describe('variants', () => {
    it('should apply info variant by default', () => {
      render(
        <ConfirmModal
          isOpen={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
          title="Info"
          message="Message"
        />
      )
      
      const confirmButton = screen.getByText('Confirm')
      expect(confirmButton).toHaveClass('bg-blue-600')
    })

    it('should apply danger variant', () => {
      render(
        <ConfirmModal
          isOpen={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
          title="Danger"
          message="Message"
          variant="danger"
        />
      )
      
      const confirmButton = screen.getByText('Confirm')
      expect(confirmButton).toHaveClass('bg-red-600')
    })

    it('should apply warning variant', () => {
      render(
        <ConfirmModal
          isOpen={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
          title="Warning"
          message="Message"
          variant="warning"
        />
      )
      
      const confirmButton = screen.getByText('Confirm')
      expect(confirmButton).toHaveClass('bg-yellow-600')
    })
  })

  describe('user interactions', () => {
    it('should call onClose when cancel button is clicked', async () => {
      const user = userEvent.setup()
      render(
        <ConfirmModal
          isOpen={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
          title="Confirm"
          message="Message"
        />
      )
      
      const cancelButton = screen.getByText('Cancel')
      await user.click(cancelButton)
      
      expect(mockOnClose).toHaveBeenCalledTimes(1)
      expect(mockOnConfirm).not.toHaveBeenCalled()
    })

    it('should call onConfirm when confirm button is clicked', async () => {
      const user = userEvent.setup()
      render(
        <ConfirmModal
          isOpen={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
          title="Confirm Action"
          message="Message"
        />
      )
      
      const confirmButton = screen.getByRole('button', { name: 'Confirm' })
      await user.click(confirmButton)
      
      expect(mockOnConfirm).toHaveBeenCalledTimes(1)
    })
  })

  describe('loading state', () => {
    it('should show loading text when isLoading is true', () => {
      render(
        <ConfirmModal
          isOpen={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
          title="Confirm"
          message="Message"
          isLoading={true}
        />
      )
      
      expect(screen.getByText('Loading...')).toBeInTheDocument()
    })

    it('should disable buttons when loading', () => {
      render(
        <ConfirmModal
          isOpen={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
          title="Confirm Action"
          message="Message"
          isLoading={true}
        />
      )
      
      // Get only the action buttons (Cancel and Confirm), not the close button
      // When loading, the confirm button text changes to "Loading..."
      const cancelButton = screen.getByRole('button', { name: 'Cancel' })
      const confirmButton = screen.getByRole('button', { name: 'Loading...' })
      
      expect(cancelButton).toBeDisabled()
      expect(confirmButton).toBeDisabled()
    })

    it('should not disable buttons when not loading', () => {
      render(
        <ConfirmModal
          isOpen={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
          title="Confirm"
          message="Message"
          isLoading={false}
        />
      )
      
      const buttons = screen.getAllByRole('button')
      buttons.forEach(button => {
        expect(button).not.toBeDisabled()
      })
    })
  })
})

