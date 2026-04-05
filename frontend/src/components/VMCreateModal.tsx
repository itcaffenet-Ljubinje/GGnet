import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { X, Loader2 } from 'lucide-react'
import { apiHelpers } from '../lib/api'
import { useNotifications } from './notifications'
import { Button } from './ui'

interface VMCreateModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
}

interface Image {
  id: number
  name: string
  description?: string
  type?: string
  image_type?: string
}

export default function VMCreateModal({ isOpen, onClose, onSuccess }: VMCreateModalProps) {
  const [formData, setFormData] = useState({
    name: '',
    system_image_id: '',
    application_image_id: '',
    vcpus: 2,
    ram_mb: 4096,
    mac_address: '',
    boot_mode: 'uefi' as 'uefi' | 'legacy',
    drives_connection: 'local' as 'local' | 'network',
    description: '',
  })

  const { addNotification } = useNotifications()

  // Fetch images
  const { data: allImages, isLoading: imagesLoading } = useQuery({
    queryKey: ['images'],
    queryFn: () => apiHelpers.getImages(),
    enabled: isOpen,
  })

  // Filter images by type
  const systemImages = allImages?.filter((img: Image) => img.image_type === 'system') || []
  const applicationImages = allImages?.filter((img: Image) => img.image_type === 'application') || []

  const createMutation = useMutation({
    mutationFn: (data: {
      name: string
      image_ids: number[]
      vcpus: number
      ram_mb: number
      mac_address?: string
      boot_mode?: string
      drives_connection?: string
      description?: string
    }) => apiHelpers.createVM(data),
    onSuccess: () => {
      addNotification({
        type: 'success',
        message: 'Virtual machine created successfully'
      })
      onSuccess()
      // Reset form
      setFormData({
        name: '',
        system_image_id: '',
        application_image_id: '',
        vcpus: 2,
        ram_mb: 4096,
        mac_address: '',
        boot_mode: 'uefi',
        drives_connection: 'local',
        description: '',
      })
    },
    onError: (error: Error) => {
      addNotification({
        type: 'error',
        message: `Failed to create VM: ${error.message}`
      })
    },
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!formData.system_image_id) {
      addNotification({
        type: 'error',
        message: 'Please select a System Image'
      })
      return
    }

    if (!formData.application_image_id) {
      addNotification({
        type: 'error',
        message: 'Please select an Application Image'
      })
      return
    }

    // Build list of image IDs (System Image + Application Image)
    const imageIds: number[] = [
      parseInt(formData.system_image_id),
      parseInt(formData.application_image_id)
    ].filter(id => !isNaN(id)) // Remove any invalid IDs

    const submitData = {
      name: formData.name,
      image_ids: imageIds,
      vcpus: formData.vcpus,
      ram_mb: formData.ram_mb,
      mac_address: formData.mac_address || undefined,
      boot_mode: formData.boot_mode,
      drives_connection: formData.drives_connection,
      description: formData.description || undefined,
    }

    createMutation.mutate(submitData)
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'number' ? parseInt(value) || 0 : value,
    }))
  }

  const handleRamSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseInt(e.target.value)
    setFormData((prev) => ({
      ...prev,
      ram_mb: value * 1024, // Convert GB to MB
    }))
  }

  const handleRamInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseInt(e.target.value) || 0
    setFormData((prev) => ({
      ...prev,
      ram_mb: value * 1024, // Convert GB to MB
    }))
  }

  if (!isOpen) return null

  const ramGb = Math.round(formData.ram_mb / 1024)
  const maxRamGb = 4 // Maximum boot RAM Size: 4 GB (as shown in the UI design)

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">Create Virtual Machine</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Name *
            </label>
            <input
              type="text"
              name="name"
              value={formData.name}
              onChange={handleInputChange}
              required
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-gray-100"
            />
          </div>

          {/* System Image */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              System Image *
            </label>
            <select
              name="system_image_id"
              value={formData.system_image_id}
              onChange={handleInputChange}
              required
              disabled={imagesLoading}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-gray-100"
            >
              <option value="">Select System Image</option>
              {systemImages.map((image: Image) => (
                <option key={image.id} value={image.id}>
                  {image.name}
                </option>
              ))}
            </select>
          </div>

          {/* Application Image */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Application Image *
            </label>
            <select
              name="application_image_id"
              value={formData.application_image_id}
              onChange={handleInputChange}
              required
              disabled={imagesLoading}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-gray-100"
            >
              <option value="">Select Application Image</option>
              {applicationImages.map((image: Image) => (
                <option key={image.id} value={image.id}>
                  {image.name}
                </option>
              ))}
            </select>
          </div>

          {/* Virtual CPUs */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Virtual CPUs number *
            </label>
            <select
              name="vcpus"
              value={formData.vcpus}
              onChange={handleInputChange}
              required
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-gray-100"
            >
              {[1, 2, 4, 6, 8, 12, 16].map((num) => (
                <option key={num} value={num}>
                  {num}
                </option>
              ))}
            </select>
          </div>

          {/* MAC Address */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              MAC Address
            </label>
            <input
              type="text"
              name="mac_address"
              value={formData.mac_address}
              onChange={handleInputChange}
              placeholder="00:11:22:33:44:55"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-gray-100"
            />
          </div>

          {/* Boot Mode */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Boot Mode *
            </label>
            <select
              name="boot_mode"
              value={formData.boot_mode}
              onChange={handleInputChange}
              required
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-gray-100"
            >
              <option value="legacy">Legacy Bios</option>
              <option value="uefi">UEFI</option>
            </select>
          </div>

          {/* Drives Connection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Drives Connection *
            </label>
            <select
              name="drives_connection"
              value={formData.drives_connection}
              onChange={handleInputChange}
              required
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-gray-100"
            >
              <option value="local">Local</option>
              <option value="network">Network</option>
            </select>
          </div>

          {/* RAM Size Configuration */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              RAM Size Configuration
            </label>
            <div className="mb-2">
              <span className="text-sm text-gray-500 dark:text-gray-400">
                Maximum boot RAM Size: {maxRamGb} GB
              </span>
            </div>
            <div className="flex items-center gap-4">
              <input
                type="range"
                min="1"
                max={maxRamGb}
                value={ramGb}
                onChange={handleRamSliderChange}
                className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
                style={{
                  background: `linear-gradient(to right, #3b82f6 0%, #3b82f6 ${(ramGb / maxRamGb) * 100}%, #e5e7eb ${(ramGb / maxRamGb) * 100}%, #e5e7eb 100%)`
                }}
              />
              <div className="flex items-center gap-2">
                <input
                  type="number"
                  min="1"
                  max={maxRamGb}
                  value={ramGb}
                  onChange={handleRamInputChange}
                  className="w-20 px-2 py-1 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-gray-100 text-right"
                />
                <span className="text-sm text-gray-700 dark:text-gray-300">GB</span>
              </div>
            </div>
          </div>

          {/* Description (optional) */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Description
            </label>
            <textarea
              name="description"
              value={formData.description}
              onChange={handleInputChange}
              rows={3}
              placeholder="VM description..."
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-gray-100"
            />
          </div>

          {/* Action Buttons */}
          <div className="flex justify-end gap-3 pt-4">
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              disabled={createMutation.isPending}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={createMutation.isPending || imagesLoading}
            >
              {createMutation.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Creating...
                </>
              ) : (
                'Create'
              )}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}

