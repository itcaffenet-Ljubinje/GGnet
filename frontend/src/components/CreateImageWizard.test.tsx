/**
 * CreateImageWizard Component Tests
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '../__tests__/setup/test-utils'
import userEvent from '@testing-library/user-event'
import { CreateImageWizard } from './CreateImageWizard'
import * as apiModule from '../lib/api'

// Mock the API module
vi.mock('../lib/api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
  },
  apiHelpers: {
    getImages: vi.fn(),
    getImage: vi.fn(),
    uploadImage: vi.fn(),
    importImage: vi.fn(),
  },
}))

// Mock notifications
vi.mock('./notifications', async () => {
  const actual = await vi.importActual('./notifications')
  return {
    ...actual,
    useNotifications: () => ({
      addNotification: vi.fn(),
    }),
  }
})

describe('CreateImageWizard', () => {
  const mockOnClose = vi.fn()
  const mockOnSuccess = vi.fn()

  const mockStorageInfo = {
    images_storage: {
      total_bytes: 1000000000, // 1GB
      used_bytes: 200000000,  // 200MB
      free_bytes: 800000000,   // 800MB
      usage_percent: 20,
    },
  }

  const mockImages = [
    { id: 1, name: 'Windows 10', image_type: 'system' },
    { id: 2, name: 'Game Image', image_type: 'application' },
  ]

  beforeEach(() => {
    vi.clearAllMocks()
    
    // Setup default mocks
    ;(apiModule.api.get as ReturnType<typeof vi.fn>).mockResolvedValue({
      data: mockStorageInfo,
    })
    ;(apiModule.apiHelpers.getImages as ReturnType<typeof vi.fn>).mockResolvedValue(mockImages)
    ;(apiModule.apiHelpers.getImage as ReturnType<typeof vi.fn>).mockResolvedValue({
      id: 1,
      name: 'Windows 10',
      file_path: '/path/to/windows10.vhdx',
    })
    ;(apiModule.apiHelpers.uploadImage as ReturnType<typeof vi.fn>).mockResolvedValue({
      id: 1,
      name: 'Test Image',
    })
    ;(apiModule.apiHelpers.importImage as ReturnType<typeof vi.fn>).mockResolvedValue({
      id: 2,
      name: 'Cloned Image',
    })
  })

  describe('rendering', () => {
    it('should not render when isOpen is false', () => {
      render(
        <CreateImageWizard
          isOpen={false}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
        />
      )

      expect(screen.queryByText(/create.*image/i)).not.toBeInTheDocument()
    })

    it('should render wizard when isOpen is true', () => {
      render(
        <CreateImageWizard
          isOpen={true}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
        />
      )

      expect(screen.getByText(/details/i)).toBeInTheDocument()
      expect(screen.getByText(/source/i)).toBeInTheDocument()
      expect(screen.getByText(/summary/i)).toBeInTheDocument()
    })

    it('should fetch storage info when opened', async () => {
      render(
        <CreateImageWizard
          isOpen={true}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
        />
      )

      await waitFor(() => {
        expect(apiModule.api.get).toHaveBeenCalledWith('/api/storage/info')
      })
    })
  })

  describe('wizard steps', () => {
    it('should show Details step initially', () => {
      render(
        <CreateImageWizard
          isOpen={true}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
        />
      )

      expect(screen.getByPlaceholderText(/enter image name/i)).toBeInTheDocument()
      expect(screen.getByText(/image type/i)).toBeInTheDocument()
      expect(screen.getByDisplayValue(/system image/i)).toBeInTheDocument()
    })

    it('should validate name is required', async () => {
      const user = userEvent.setup()
      render(
        <CreateImageWizard
          isOpen={true}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
        />
      )

      const nextButton = screen.getByRole('button', { name: /next/i })
      await user.click(nextButton)

      // Should stay on Details step if name is empty
      await waitFor(() => {
        expect(screen.getByPlaceholderText(/enter image name/i)).toBeInTheDocument()
      })
    })

    it('should allow entering image name', async () => {
      const user = userEvent.setup()
      render(
        <CreateImageWizard
          isOpen={true}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
        />
      )

      const nameInput = screen.getByPlaceholderText(/enter image name/i)
      await user.type(nameInput, 'My Test Image')

      expect(nameInput).toHaveValue('My Test Image')
    })

    it('should show OS template dropdown for SYSTEM images', async () => {
      const user = userEvent.setup()
      render(
        <CreateImageWizard
          isOpen={true}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
        />
      )

      // Fill in name and go to source step
      const nameInput = screen.getByPlaceholderText(/enter image name/i)
      await user.type(nameInput, 'Test Image')

      const nextButton = screen.getByRole('button', { name: /next/i })
      await user.click(nextButton)

      await waitFor(() => {
        expect(screen.getByLabelText(/os template/i)).toBeInTheDocument()
        const osTemplateSelect = screen.getByLabelText(/os template/i) as HTMLSelectElement
        expect(osTemplateSelect).toBeInTheDocument()
        expect(osTemplateSelect.value).toBe('')
      }, { timeout: 3000 })
    })

    it('should not show OS template for APPLICATION images', async () => {
      const user = userEvent.setup()
      render(
        <CreateImageWizard
          isOpen={true}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
        />
      )

      // Change to APPLICATION type
      const typeSelect = screen.getByDisplayValue(/system image/i)
      await user.selectOptions(typeSelect, 'APPLICATION')

      // Fill in name and go to source step
      const nameInput = screen.getByPlaceholderText(/enter image name/i)
      await user.type(nameInput, 'Test Image')

      const nextButton = screen.getByRole('button', { name: /next/i })
      await user.click(nextButton)

      await waitFor(() => {
        expect(screen.queryByText(/os template/i)).not.toBeInTheDocument()
      })
    })
  })

  describe('source selection', () => {
    it('should show upload and clone options', async () => {
      const user = userEvent.setup()
      render(
        <CreateImageWizard
          isOpen={true}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
        />
      )

      // Fill in name and go to source step
      const nameInput = screen.getByPlaceholderText(/enter image name/i)
      await user.type(nameInput, 'Test Image')

      const nextButton = screen.getByRole('button', { name: /next/i })
      await user.click(nextButton)

      await waitFor(() => {
        expect(screen.getByText(/upload file/i)).toBeInTheDocument()
        expect(screen.getByText(/clone existing/i)).toBeInTheDocument()
      })
    })

    it('should show file input when upload is selected', async () => {
      const user = userEvent.setup()
      render(
        <CreateImageWizard
          isOpen={true}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
        />
      )

      // Fill in name and go to source step
      const nameInput = screen.getByPlaceholderText(/enter image name/i)
      await user.type(nameInput, 'Test Image')

      const nextButton = screen.getByRole('button', { name: /next/i })
      await user.click(nextButton)

      // Wait for source step to load - check for source type label
      await waitFor(() => {
        expect(screen.getByText(/source type/i)).toBeInTheDocument()
      }, { timeout: 3000 })

      // File input should be visible by default (upload is selected by default)
      await waitFor(() => {
        const fileInput = screen.getByLabelText(/image file/i) as HTMLInputElement
        expect(fileInput).toBeInTheDocument()
        expect(fileInput.type).toBe('file')
      }, { timeout: 3000 })
    })

    it('should show image selector when clone is selected', async () => {
      const user = userEvent.setup()
      render(
        <CreateImageWizard
          isOpen={true}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
        />
      )

      // Fill in name and go to source step
      const nameInput = screen.getByPlaceholderText(/enter image name/i)
      await user.type(nameInput, 'Test Image')

      const nextButton = screen.getByRole('button', { name: /next/i })
      await user.click(nextButton)

      // Click clone option
      await waitFor(() => {
        const cloneCard = screen.getByText(/clone existing/i).closest('div')
        expect(cloneCard).toBeInTheDocument()
      })

      const cloneCard = screen.getByText(/clone existing/i).closest('div')
      if (cloneCard) {
        await user.click(cloneCard)
      }

      await waitFor(() => {
        expect(apiModule.apiHelpers.getImages).toHaveBeenCalled()
      }, { timeout: 3000 })

      await waitFor(() => {
        expect(screen.getByText(/source image/i)).toBeInTheDocument()
        const sourceSelect = screen.getByLabelText(/source image/i) as HTMLSelectElement
        expect(sourceSelect).toBeInTheDocument()
      }, { timeout: 3000 })
    })
  })

  describe('file upload', () => {
    it('should allow selecting a file', async () => {
      const user = userEvent.setup()
      render(
        <CreateImageWizard
          isOpen={true}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
        />
      )

      // Fill in name and go to source step
      const nameInput = screen.getByPlaceholderText(/enter image name/i)
      await user.type(nameInput, 'Test Image')

      const nextButton = screen.getByRole('button', { name: /next/i })
      await user.click(nextButton)

      await waitFor(() => {
        const fileInput = screen.getByLabelText(/image file/i) as HTMLInputElement
        expect(fileInput).toBeInTheDocument()
        expect(fileInput.type).toBe('file')
      }, { timeout: 3000 })

      const fileInput = screen.getByLabelText(/image file/i) as HTMLInputElement
      const file = new File(['test content'], 'test.vhdx', { type: 'application/octet-stream' })
      
      await user.upload(fileInput, file)

      await waitFor(() => {
        expect(fileInput.files?.[0]).toBe(file)
      })
    })

    it('should show file size after selection', async () => {
      const user = userEvent.setup()
      render(
        <CreateImageWizard
          isOpen={true}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
        />
      )

      // Fill in name and go to source step
      const nameInput = screen.getByPlaceholderText(/enter image name/i)
      await user.type(nameInput, 'Test Image')

      const nextButton = screen.getByRole('button', { name: /next/i })
      await user.click(nextButton)

      await waitFor(() => {
        const fileInput = screen.getByLabelText(/image file/i) as HTMLInputElement
        expect(fileInput).toBeInTheDocument()
        expect(fileInput.type).toBe('file')
      }, { timeout: 3000 })

      const fileInput = screen.getByLabelText(/image file/i) as HTMLInputElement
      const file = new File(['test content'], 'test.vhdx', { type: 'application/octet-stream' })
      
      await user.upload(fileInput, file)

      await waitFor(() => {
        expect(screen.getByText(/selected:/i)).toBeInTheDocument()
        expect(screen.getByText(/test\.vhdx/i)).toBeInTheDocument()
      }, { timeout: 3000 })
    })
  })

  describe('storage validation', () => {
    it('should show storage warning when usage is high', async () => {
      const highUsageStorage = {
        images_storage: {
          total_bytes: 1000000000,
          used_bytes: 950000000, // 95% used
          free_bytes: 50000000,
          usage_percent: 95,
        },
      }

      ;(apiModule.api.get as ReturnType<typeof vi.fn>).mockResolvedValue({
        data: highUsageStorage,
      })

      const user = userEvent.setup()
      render(
        <CreateImageWizard
          isOpen={true}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
        />
      )

      // Fill in name and go to source step
      const nameInput = screen.getByPlaceholderText(/enter image name/i)
      await user.type(nameInput, 'Test Image')

      const nextButton = screen.getByRole('button', { name: /next/i })
      await user.click(nextButton)

      await waitFor(() => {
        const fileInput = screen.getByLabelText(/image file/i) as HTMLInputElement
        expect(fileInput).toBeInTheDocument()
        expect(fileInput.type).toBe('file')
      }, { timeout: 3000 })

      const fileInput = screen.getByLabelText(/image file/i) as HTMLInputElement
      const file = new File(['test content'], 'test.vhdx', { type: 'application/octet-stream' })
      
      await user.upload(fileInput, file)

      await waitFor(() => {
        // Should show storage warning - check for storage warning/error title
        // The warning shows "Storage Warning" or "Storage Error" as title
        const storageTitle = screen.queryByText(/storage warning|storage error/i)
        expect(storageTitle).toBeInTheDocument()
      }, { timeout: 5000 })
    })
  })

  describe('wizard navigation', () => {
    it('should navigate to next step when Next is clicked', async () => {
      const user = userEvent.setup()
      render(
        <CreateImageWizard
          isOpen={true}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
        />
      )

      const nameInput = screen.getByPlaceholderText(/enter image name/i)
      await user.type(nameInput, 'Test Image')

      const nextButton = screen.getByRole('button', { name: /next/i })
      await user.click(nextButton)

      await waitFor(() => {
        expect(screen.getByText(/source type/i)).toBeInTheDocument()
      }, { timeout: 3000 })
      
      // Check for upload/clone cards - use getAllByText since there might be multiple
      await waitFor(() => {
        const uploadTexts = screen.getAllByText(/upload file/i)
        const cloneTexts = screen.getAllByText(/clone existing/i)
        expect(uploadTexts.length).toBeGreaterThan(0)
        expect(cloneTexts.length).toBeGreaterThan(0)
      }, { timeout: 2000 })
    })

    it('should navigate back to previous step', async () => {
      const user = userEvent.setup()
      render(
        <CreateImageWizard
          isOpen={true}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
        />
      )

      // Go to step 2
      const nameInput = screen.getByPlaceholderText(/enter image name/i)
      await user.type(nameInput, 'Test Image')

      const nextButton = screen.getByRole('button', { name: /next/i })
      await user.click(nextButton)

      await waitFor(() => {
        expect(screen.getByText(/source type/i)).toBeInTheDocument()
      }, { timeout: 3000 })

      // Go back
      const backButton = screen.getByRole('button', { name: /previous/i })
      await user.click(backButton)

      await waitFor(() => {
        expect(screen.getByPlaceholderText(/enter image name/i)).toBeInTheDocument()
        expect(screen.getByLabelText(/image type/i)).toBeInTheDocument()
      }, { timeout: 3000 })
    })

    it('should close wizard when Cancel is clicked', async () => {
      const user = userEvent.setup()
      render(
        <CreateImageWizard
          isOpen={true}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
        />
      )

      const cancelButton = screen.getByRole('button', { name: /cancel/i })
      await user.click(cancelButton)

      expect(mockOnClose).toHaveBeenCalled()
    })
  })

  describe('image creation', () => {
    it('should upload image when form is submitted', async () => {
      const user = userEvent.setup()
      render(
        <CreateImageWizard
          isOpen={true}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
        />
      )

      // Step 1: Details
      const nameInput = screen.getByPlaceholderText(/enter image name/i)
      await user.type(nameInput, 'Test Image')

      const nextButton = screen.getByRole('button', { name: /next/i })
      await user.click(nextButton)

      // Step 2: Source
      await waitFor(() => {
        const fileInput = screen.getByLabelText(/image file/i) as HTMLInputElement
        expect(fileInput).toBeInTheDocument()
      }, { timeout: 3000 })

      const fileInput = screen.getByLabelText(/image file/i) as HTMLInputElement
      const file = new File(['test content'], 'test.vhdx', { type: 'application/octet-stream' })
      await user.upload(fileInput, file)

      await user.click(screen.getByRole('button', { name: /next/i }))

      // Step 3: Summary
      await waitFor(() => {
        expect(screen.getByText(/summary/i)).toBeInTheDocument()
      })

      const completeButton = screen.getByRole('button', { name: /complete/i })
      await user.click(completeButton)

      await waitFor(() => {
        expect(apiModule.apiHelpers.uploadImage).toHaveBeenCalled()
      })
    })

    it('should clone image when clone option is selected', async () => {
      const user = userEvent.setup()
      render(
        <CreateImageWizard
          isOpen={true}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
        />
      )

      // Step 1: Details
      const nameInput = screen.getByPlaceholderText(/enter image name/i)
      await user.type(nameInput, 'Cloned Image')

      const nextButton = screen.getByRole('button', { name: /next/i })
      await user.click(nextButton)

      // Step 2: Source - Select clone
      await waitFor(() => {
        const cloneCard = screen.getByText(/clone existing/i).closest('div')
        expect(cloneCard).toBeInTheDocument()
      })

      const cloneCard = screen.getByText(/clone existing/i).closest('div')
      if (cloneCard) {
        await user.click(cloneCard)
      }

      // Wait for source image select to appear after clone is selected
      await waitFor(() => {
        expect(screen.getByText(/source image/i)).toBeInTheDocument()
      }, { timeout: 5000 })

      // Wait for select element to be available
      await waitFor(() => {
        const sourceSelect = screen.getByLabelText(/source image/i) as HTMLSelectElement
        expect(sourceSelect).toBeInTheDocument()
      }, { timeout: 3000 })

      // Wait for options to load (images are fetched when clone is selected)
      const sourceSelect = screen.getByLabelText(/source image/i) as HTMLSelectElement
      await waitFor(() => {
        // Should have at least placeholder + mock images (2 images)
        expect(sourceSelect.options.length).toBeGreaterThan(1)
      }, { timeout: 5000 })

      // Select the first image option (value is '1')
      await user.selectOptions(sourceSelect, '1')

      await waitFor(() => {
        expect(sourceSelect.value).toBe('1')
      }, { timeout: 2000 })

      // Navigate to summary
      const nextButtonToSummary = screen.getByRole('button', { name: /next/i })
      await user.click(nextButtonToSummary)

      // Step 3: Summary - wait for summary step
      await waitFor(() => {
        expect(screen.getByText(/summary/i)).toBeInTheDocument()
      }, { timeout: 3000 })

      // Complete the wizard
      const completeButton = screen.getByRole('button', { name: /complete/i })
      await user.click(completeButton)

      // Wait for API call - importImage should be called with correct data
      await waitFor(() => {
        expect(apiModule.apiHelpers.importImage).toHaveBeenCalled()
        const callArgs = (apiModule.apiHelpers.importImage as ReturnType<typeof vi.fn>).mock.calls[0]?.[0]
        expect(callArgs).toBeDefined()
        expect(callArgs?.name).toBe('Cloned Image')
      }, { timeout: 5000 })
    })
  })
})




