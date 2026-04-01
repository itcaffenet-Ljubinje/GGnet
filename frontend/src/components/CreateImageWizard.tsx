/**
 * CreateImageWizard Component
 * Multi-step wizard for creating new disk images
 */

import { useState, ReactNode } from 'react'
import { Modal } from './ui/Modal'
import { Wizard, type WizardStep } from './ui/Wizard'
import { Input } from './ui/Input'
import { Button } from './ui/Button'
import { Card } from './ui/Card'
import { StatusBadge } from './ui/StatusBadge'
import { ProgressBar } from './ui/ProgressBar'
import { AlertTriangle, Info, Upload, Copy, HardDrive, CheckCircle, Loader2 } from 'lucide-react'
import { clsx } from 'clsx'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../lib/api'
import { apiHelpers } from '../lib/api'
import { formatBytes } from '../utils/formatters'
import { useNotifications } from './notifications'

interface CreateImageWizardProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
}

interface ImageFormData {
  name: string
  description: string
  image_type: 'SYSTEM' | 'APPLICATION' | 'DATA'
  source_type: 'upload' | 'clone'
  source_image_id?: number
  os_template?: string
  file?: File
}

export function CreateImageWizard({ isOpen, onClose, onSuccess }: CreateImageWizardProps) {
  const [formData, setFormData] = useState<ImageFormData>({
    name: '',
    description: '',
    image_type: 'SYSTEM',
    source_type: 'upload',
  })
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const queryClient = useQueryClient()
  const { addNotification } = useNotifications()

  // Fetch existing images for cloning
  const { data: existingImages } = useQuery({
    queryKey: ['images'],
    queryFn: () => apiHelpers.getImages(),
    enabled: isOpen && formData.source_type === 'clone',
  })

  // Fetch storage info for validation
  const { data: storageInfo } = useQuery({
    queryKey: ['storage', 'info'],
    queryFn: () => api.get('/api/storage/info').then(res => res.data).catch(() => null),
    enabled: isOpen,
  })

  // Calculate storage validation
  const getStorageValidation = () => {
    if (!storageInfo || !formData.file) return null

    const imagesStorage = storageInfo.images_storage || storageInfo.imagesStorage
    if (!imagesStorage) return null

    const fileSize = formData.file.size
    const freeSpace = imagesStorage.free_bytes || imagesStorage.freeBytes || 0
    const usagePercent = imagesStorage.usage_percent || imagesStorage.usagePercent || 0
    const threshold = 20 // 20% warning threshold

    // Check if there's enough space
    if (freeSpace < fileSize) {
      return {
        level: 'error' as const,
        message: `Insufficient storage space. File size: ${formatBytes(fileSize)}, Available: ${formatBytes(freeSpace)}`,
        canProceed: false
      }
    }

    // Check if usage is above threshold
    if (usagePercent > threshold) {
      return {
        level: 'warning' as const,
        message: `Storage usage is at ${usagePercent.toFixed(1)}%, above the ${threshold}% warning threshold. Available: ${formatBytes(freeSpace)}`,
        canProceed: true
      }
    }

    // Check if usage will exceed threshold after upload
    const projectedUsage = ((imagesStorage.used_bytes || imagesStorage.usedBytes || 0) + fileSize) / (imagesStorage.total_bytes || imagesStorage.totalBytes || 1) * 100
    if (projectedUsage > threshold) {
      return {
        level: 'warning' as const,
        message: `Uploading this file will bring storage usage to ${projectedUsage.toFixed(1)}%, above the ${threshold}% threshold.`,
        canProceed: true
      }
    }

    return null
  }

  const storageValidation = getStorageValidation()

  // Upload image mutation
  const uploadImageMutation = useMutation({
    mutationFn: async (formDataToUpload: FormData) => {
      setUploadProgress(0)
      return apiHelpers.uploadImage(formDataToUpload, {
        onProgress: (progress) => {
          setUploadProgress(progress)
        }
      })
    },
    onSuccess: (data) => {
      setUploadProgress(100)
      queryClient.invalidateQueries({ queryKey: ['images'] })
      addNotification({
        type: 'success',
        message: `Image "${data.name}" created successfully`
      })
      // Small delay to show 100% progress
      setTimeout(() => {
        onSuccess()
        onClose()
        resetForm()
        setUploadProgress(0)
      }, 500)
    },
    onError: (error: Error) => {
      const errorMessage = (error as { response?: { data?: { detail?: string } } }).response?.data?.detail || error.message
      addNotification({
        type: 'error',
        message: `Failed to create image: ${errorMessage}`
      })
      setIsSubmitting(false)
    },
  })

  // Clone image mutation (using import endpoint)
  const cloneImageMutation = useMutation({
    mutationFn: async (data: { name: string; description?: string; image_type: string; source_image_id: number }) => {
      // First get the source image to get its path
      const sourceImage = await apiHelpers.getImage(data.source_image_id) as { file_path?: string }
      
      // Use import endpoint to clone
      // Backend expects lowercase: 'system', 'application', 'data'
      // ImageResponse now includes file_path field
      if (!sourceImage?.file_path) {
        throw new Error('Source image file_path not found. The image may not be available for cloning.')
      }
      
      return apiHelpers.importImage({
        name: data.name,
        description: data.description,
        image_type: data.image_type.toLowerCase(), // Backend ImageType enum uses lowercase
        source_path: sourceImage.file_path,
      })
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['images'] })
      addNotification({
        type: 'success',
        message: `Image "${data.name}" cloned successfully`
      })
      onSuccess()
      onClose()
      resetForm()
    },
    onError: (error: Error) => {
      const errorMessage = (error as { response?: { data?: { detail?: string } } }).response?.data?.detail || error.message
      addNotification({
        type: 'error',
        message: `Failed to clone image: ${errorMessage}`
      })
      setIsSubmitting(false)
    },
  })

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      image_type: 'SYSTEM',
      source_type: 'upload',
    })
    setIsSubmitting(false)
    setUploadProgress(0)
  }

  const handleInputChange = (field: keyof ImageFormData, value: string | File) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      handleInputChange('file', file)
    }
  }

  const validateDetails = () => {
    return formData.name.trim().length > 0
  }

  const validateSource = () => {
    if (formData.source_type === 'upload') {
      if (!formData.file) return false
      // Check storage validation if available
      if (storageValidation && storageValidation.level === 'error') {
        return false
      }
      return true
    } else {
      return !!formData.source_image_id
    }
  }

  const getStorageWarning = () => {
    if (!storageInfo || formData.image_type !== 'APPLICATION') return null
    
    const availableSpace = storageInfo.available_space || 0
    const reservedSpace = storageInfo.reserved_space || 0
    const threshold = storageInfo.warning_threshold || 20 // 20% default
    
    const usagePercent = ((storageInfo.used_space || 0) / (storageInfo.total_space || 1)) * 100
    
    if (usagePercent > threshold) {
      return {
        level: 'warning' as const,
        message: `Storage usage is at ${usagePercent.toFixed(1)}%, above the ${threshold}% warning threshold.`
      }
    }
    
    return null
  }

  const storageWarning = getStorageWarning()

  // Step 1: Details
  const detailsStep: WizardStep = {
    id: 'details',
    title: 'Details',
    description: 'Enter basic information about the image',
    content: (
      <div className="space-y-4">
        <div>
          <label htmlFor="image-name-input" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Image Name *
          </label>
          <Input
            id="image-name-input"
            type="text"
            value={formData.name}
            onChange={(e) => handleInputChange('name', e.target.value)}
            placeholder="Enter image name"
            required
          />
        </div>

        <div>
          <label htmlFor="image-type-select" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Image Type *
          </label>
          <select
            id="image-type-select"
            value={formData.image_type}
            onChange={(e) => handleInputChange('image_type', e.target.value as ImageFormData['image_type'])}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="SYSTEM">System Image</option>
            <option value="APPLICATION">Application/Game Image</option>
            <option value="DATA">Data Image</option>
          </select>
        </div>

        {formData.image_type === 'APPLICATION' && (
          <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
            <div className="flex items-start">
              <AlertTriangle className="w-5 h-5 text-yellow-600 mr-2 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-yellow-800 dark:text-yellow-200">
                  Storage Impact Warning
                </p>
                <p className="text-sm text-yellow-700 dark:text-yellow-300 mt-1">
                  Application images can be large and will consume significant storage space. 
                  Ensure you have adequate free space available.
                </p>
                {storageWarning && (
                  <p className="text-sm text-yellow-700 dark:text-yellow-300 mt-2 font-medium">
                    {storageWarning.message}
                  </p>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Storage Validation */}
        {formData.source_type === 'upload' && formData.file && storageValidation && (
          <div className={clsx(
            'border rounded-lg p-4',
            storageValidation.level === 'error' 
              ? 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800'
              : 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800'
          )}>
            <div className="flex items-start">
              <AlertTriangle className={clsx(
                'w-5 h-5 mr-2 mt-0.5',
                storageValidation.level === 'error' ? 'text-red-600' : 'text-yellow-600'
              )} />
              <div>
                <p className={clsx(
                  'text-sm font-medium',
                  storageValidation.level === 'error'
                    ? 'text-red-800 dark:text-red-200'
                    : 'text-yellow-800 dark:text-yellow-200'
                )}>
                  {storageValidation.level === 'error' ? 'Storage Error' : 'Storage Warning'}
                </p>
                <p className={clsx(
                  'text-sm mt-1',
                  storageValidation.level === 'error'
                    ? 'text-red-700 dark:text-red-300'
                    : 'text-yellow-700 dark:text-yellow-300'
                )}>
                  {storageValidation.message}
                </p>
                {storageInfo?.images_storage && (
                  <div className="mt-2">
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-gray-600 dark:text-gray-400">Storage Usage</span>
                      <span className="font-medium">
                        {((storageInfo.images_storage.used_bytes || 0) / (storageInfo.images_storage.total_bytes || 1) * 100).toFixed(1)}%
                      </span>
                    </div>
                    <ProgressBar 
                      progress={(storageInfo.images_storage.used_bytes || 0) / (storageInfo.images_storage.total_bytes || 1) * 100}
                      className="h-2"
                    />
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Description
          </label>
          <textarea
            value={formData.description}
            onChange={(e) => handleInputChange('description', e.target.value)}
            placeholder="Optional description"
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>
    ),
    isValid: validateDetails,
  }

  // Step 2: Source
  const sourceStep: WizardStep = {
    id: 'source',
    title: 'Source',
    description: 'Choose how to create the image',
    content: (
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
            Source Type *
          </label>
          <div className="grid grid-cols-2 gap-4">
            <Card
              className={clsx(
                'p-4 cursor-pointer border-2 transition-colors',
                formData.source_type === 'upload'
                  ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                  : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
              )}
              onClick={() => handleInputChange('source_type', 'upload')}
            >
              <div className="flex items-center mb-2">
                <Upload className="w-5 h-5 mr-2 text-blue-500" />
                <h3 className="font-medium text-gray-900 dark:text-gray-100">Upload File</h3>
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Upload an existing disk image file (VHDX, RAW, QCOW2)
              </p>
            </Card>

            <Card
              className={clsx(
                'p-4 cursor-pointer border-2 transition-colors',
                formData.source_type === 'clone'
                  ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                  : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
              )}
              onClick={() => handleInputChange('source_type', 'clone')}
            >
              <div className="flex items-center mb-2">
                <Copy className="w-5 h-5 mr-2 text-green-500" />
                <h3 className="font-medium text-gray-900 dark:text-gray-100">Clone Existing</h3>
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Create a copy from an existing image
              </p>
            </Card>
          </div>
        </div>

        {formData.source_type === 'upload' && (
          <div>
            <label htmlFor="image-file-input" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Image File *
            </label>
            <input
              id="image-file-input"
              type="file"
              onChange={handleFileSelect}
              accept=".vhdx,.raw,.qcow2"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            {formData.file && (
              <p className="mt-2 text-sm text-gray-600">
                Selected: {formData.file.name} ({formatBytes(formData.file.size)})
              </p>
            )}
          </div>
        )}

        {formData.source_type === 'clone' && (
          <div>
            <label htmlFor="source-image-select" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Source Image *
            </label>
            <select
              id="source-image-select"
              value={formData.source_image_id || ''}
              onChange={(e) => handleInputChange('source_image_id', parseInt(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Select an image to clone...</option>
              {(Array.isArray(existingImages) ? existingImages : existingImages?.images || existingImages?.data || []).map((img: { id: number; name: string; image_type: string }) => (
                <option key={img.id} value={img.id}>
                  {img.name} ({img.image_type})
                </option>
              ))}
            </select>
          </div>
        )}

        {formData.image_type === 'SYSTEM' && formData.source_type === 'upload' && (
          <div>
            <label htmlFor="os-template-select" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              OS Template (Optional)
            </label>
            <select
              id="os-template-select"
              value={formData.os_template || ''}
              onChange={(e) => handleInputChange('os_template', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">None</option>
              <option value="windows-10">Windows 10</option>
              <option value="windows-11">Windows 11</option>
              <option value="windows-server-2019">Windows Server 2019</option>
              <option value="windows-server-2022">Windows Server 2022</option>
            </select>
            <p className="mt-1 text-xs text-gray-500">
              Select an OS template to apply standard configurations
            </p>
          </div>
        )}

        {formData.image_type === 'APPLICATION' && (
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
            <div className="flex items-start">
              <Info className="w-5 h-5 text-blue-600 mr-2 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-blue-800 dark:text-blue-200">
                  Native Creation Flow
                </p>
                <p className="text-sm text-blue-700 dark:text-blue-300 mt-1">
                  For game images, consider using the native creation flow which provides better 
                  optimization and compression. This wizard is suitable for quick uploads.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    ),
    isValid: validateSource,
  }

  // Step 3: Summary
  const summaryStep: WizardStep = {
    id: 'summary',
    title: 'Summary',
    description: 'Review and confirm your image creation',
    content: (
      <div className="space-y-4">
        <Card className="p-4">
          <h3 className="font-medium text-gray-900 dark:text-gray-100 mb-4">Image Details</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">Name:</span>
              <span className="font-medium text-gray-900 dark:text-gray-100">{formData.name}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">Type:</span>
              <StatusBadge status="info" text={formData.image_type} />
            </div>
            {formData.description && (
              <div className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400">Description:</span>
                <span className="font-medium text-gray-900 dark:text-gray-100">{formData.description}</span>
              </div>
            )}
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">Source:</span>
              <span className="font-medium text-gray-900 dark:text-gray-100">
                {formData.source_type === 'upload' ? 'File Upload' : 'Clone from Existing'}
              </span>
            </div>
            {formData.source_type === 'upload' && formData.file && (
              <div className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400">File:</span>
                <span className="font-medium text-gray-900 dark:text-gray-100">
                  {formData.file.name} ({formatBytes(formData.file.size)})
                </span>
              </div>
            )}
            {formData.source_type === 'clone' && formData.source_image_id && (
              <div className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400">Source Image ID:</span>
                <span className="font-medium text-gray-900 dark:text-gray-100">#{formData.source_image_id}</span>
              </div>
            )}
            {formData.os_template && (
              <div className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400">OS Template:</span>
                <span className="font-medium text-gray-900 dark:text-gray-100">{formData.os_template}</span>
              </div>
            )}
          </div>
        </Card>

        {storageWarning && (
          <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
            <div className="flex items-start">
              <AlertTriangle className="w-5 h-5 text-yellow-600 mr-2 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-yellow-800 dark:text-yellow-200">
                  Storage Warning
                </p>
                <p className="text-sm text-yellow-700 dark:text-yellow-300 mt-1">
                  {storageWarning.message}
                </p>
              </div>
            </div>
          </div>
        )}

        <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Click "Complete" to create the image. This process may take several minutes depending on the image size.
          </p>
        </div>
      </div>
    ),
    isValid: () => true,
  }

  const handleComplete = async (data: Record<string, unknown>) => {
    setIsSubmitting(true)

    try {
      if (formData.source_type === 'upload') {
        // Upload new image
        if (!formData.file) {
          addNotification({
            type: 'error',
            message: 'Please select a file to upload'
          })
          setIsSubmitting(false)
          return
        }

        const uploadFormData = new FormData()
        uploadFormData.append('file', formData.file)
        uploadFormData.append('name', formData.name)
        // Backend expects lowercase: 'system', 'application', 'data'
        uploadFormData.append('image_type', formData.image_type.toLowerCase())
        if (formData.description) {
          uploadFormData.append('description', formData.description)
        }
        // Add OS template if provided
        if (formData.os_template && formData.image_type === 'SYSTEM') {
          uploadFormData.append('os_template', formData.os_template)
        }

        await uploadImageMutation.mutateAsync(uploadFormData)
      } else {
        // Clone existing image
        if (!formData.source_image_id) {
          addNotification({
            type: 'error',
            message: 'Please select a source image to clone'
          })
          setIsSubmitting(false)
          return
        }

        await cloneImageMutation.mutateAsync({
          name: formData.name,
          description: formData.description,
          image_type: formData.image_type,
          source_image_id: formData.source_image_id,
        })
      }
    } catch (error) {
      // Error handling is done in mutation onError
      console.error('Failed to create image:', error)
    }
  }

  const steps: WizardStep[] = [detailsStep, sourceStep, summaryStep]

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Create New Image"
      size="lg"
    >
      <Wizard
        steps={steps}
        onComplete={handleComplete}
        onCancel={onClose}
      />
    </Modal>
  )
}




