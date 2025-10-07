import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle, Button } from './ui'
import { X, Save, Loader2 } from 'lucide-react'
import { apiHelpers } from '../lib/api'
import { useNotifications } from './notifications'

interface Machine {
  id?: number;
  name: string;
  hostname: string;
  ip_address: string;
  mac_address: string;
  asset_tag?: string;
  description?: string;
  boot_mode?: string;
  secure_boot_enabled?: boolean;
  location?: string;
  room?: string;
  auto_boot?: boolean;
  wake_on_lan?: boolean;
}

interface MachineModalProps {
  isOpen: boolean
  onClose: () => void
  machine?: Machine | null
  mode: 'create' | 'edit'
}

export default function MachineModal({ isOpen, onClose, machine, mode }: MachineModalProps) {
  const [formData, setFormData] = useState({
    name: machine?.name || '',
    description: machine?.description || '',
    mac_address: machine?.mac_address || '',
    ip_address: machine?.ip_address || '',
    hostname: machine?.hostname || '',
    boot_mode: machine?.boot_mode || 'uefi',
    secure_boot_enabled: machine?.secure_boot_enabled || false,
    location: machine?.location || '',
    room: machine?.room || '',
    asset_tag: machine?.asset_tag || '',
    auto_boot: machine?.auto_boot || false,
    wake_on_lan: machine?.wake_on_lan || true,
    ...machine
  })

  const [isSubmitting, setIsSubmitting] = useState(false)
  const { addNotification } = useNotifications()
  const queryClient = useQueryClient()

  const createMutation = useMutation({
    mutationFn: (data: { name: string; hostname: string; ip_address: string; mac_address: string; asset_tag?: string; description?: string }) => apiHelpers.createMachine(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['machines'] })
      addNotification({
        type: 'success',
        message: 'Machine created successfully'
      })
      onClose()
    },
    onError: (error: Error) => {
      addNotification({
        type: 'error',
        message: `Failed to create machine: ${error.message}`
      })
    }
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: { name: string; hostname: string; ip_address: string; mac_address: string; asset_tag?: string; description?: string } }) => apiHelpers.updateMachine(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['machines'] })
      addNotification({
        type: 'success',
        message: 'Machine updated successfully'
      })
      onClose()
    },
    onError: (error: Error) => {
      addNotification({
        type: 'error',
        message: `Failed to update machine: ${error.message}`
      })
    }
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)

    try {
      if (mode === 'create') {
        await createMutation.mutateAsync(formData)
      } else {
        await updateMutation.mutateAsync({ id: machine.id, data: formData })
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target
    setFormData((prev: typeof formData) => ({
      ...prev,
      [name]: type === 'checkbox' ? (e.target as HTMLInputElement).checked : value
    }))
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>
              {mode === 'create' ? 'Add New Machine' : 'Edit Machine'}
            </CardTitle>
            <Button
              variant="outline"
              size="sm"
              onClick={onClose}
              className="h-8 w-8 p-0"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Machine Name *
                </label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-800 dark:text-gray-100"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  MAC Address *
                </label>
                <input
                  type="text"
                  name="mac_address"
                  value={formData.mac_address}
                  onChange={handleInputChange}
                  required
                  placeholder="00:11:22:33:44:55"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-800 dark:text-gray-100"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  IP Address
                </label>
                <input
                  type="text"
                  name="ip_address"
                  value={formData.ip_address}
                  onChange={handleInputChange}
                  placeholder="192.168.1.100"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-800 dark:text-gray-100"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Hostname
                </label>
                <input
                  type="text"
                  name="hostname"
                  value={formData.hostname}
                  onChange={handleInputChange}
                  placeholder="machine-01"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-800 dark:text-gray-100"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Boot Mode
                </label>
                <select
                  name="boot_mode"
                  value={formData.boot_mode}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-800 dark:text-gray-100"
                >
                  <option value="uefi">UEFI</option>
                  <option value="legacy">Legacy BIOS</option>
                  <option value="auto">Auto</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Asset Tag
                </label>
                <input
                  type="text"
                  name="asset_tag"
                  value={formData.asset_tag}
                  onChange={handleInputChange}
                  placeholder="ASSET-001"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-800 dark:text-gray-100"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Location
                </label>
                <input
                  type="text"
                  name="location"
                  value={formData.location}
                  onChange={handleInputChange}
                  placeholder="Building A, Floor 2"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-800 dark:text-gray-100"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Room
                </label>
                <input
                  type="text"
                  name="room"
                  value={formData.room}
                  onChange={handleInputChange}
                  placeholder="Room 201"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-800 dark:text-gray-100"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Description
              </label>
              <textarea
                name="description"
                value={formData.description}
                onChange={handleInputChange}
                rows={3}
                placeholder="Machine description..."
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-800 dark:text-gray-100"
              />
            </div>

            <div className="flex items-center space-x-6">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  name="secure_boot_enabled"
                  checked={formData.secure_boot_enabled}
                  onChange={handleInputChange}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                  Secure Boot Enabled
                </span>
              </label>

              <label className="flex items-center">
                <input
                  type="checkbox"
                  name="auto_boot"
                  checked={formData.auto_boot}
                  onChange={handleInputChange}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                  Auto Boot
                </span>
              </label>

              <label className="flex items-center">
                <input
                  type="checkbox"
                  name="wake_on_lan"
                  checked={formData.wake_on_lan}
                  onChange={handleInputChange}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                  Wake on LAN
                </span>
              </label>
            </div>

            <div className="flex justify-end space-x-3 pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={onClose}
                disabled={isSubmitting}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={isSubmitting}
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    {mode === 'create' ? 'Creating...' : 'Updating...'}
                  </>
                ) : (
                  <>
                    <Save className="h-4 w-4 mr-2" />
                    {mode === 'create' ? 'Create Machine' : 'Update Machine'}
                  </>
                )}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
