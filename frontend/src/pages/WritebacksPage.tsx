import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiHelpers } from '../lib/api'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card'
import { LoadingSpinner } from '../components/LoadingSpinner'
import { FileText, Trash2, Save, HardDrive, Monitor, AlertCircle, CheckCircle } from 'lucide-react'
import toast from 'react-hot-toast'

interface Writeback {
  id: number
  machine_id: number
  image_id: number
  path: string
  size: number
  created_at: string
  machine?: {
    name: string
  }
  image?: {
    name: string
  }
}

export default function WritebacksPage() {
  const [selectedMachineId, setSelectedMachineId] = useState<number | undefined>()
  const [selectedImageId, setSelectedImageId] = useState<number | undefined>()
  const queryClient = useQueryClient()

  const { data: writebacks, isLoading } = useQuery({
    queryKey: ['writebacks', selectedMachineId, selectedImageId],
    queryFn: () => apiHelpers.getWritebacks({
      machine_id: selectedMachineId,
      image_id: selectedImageId,
    }),
  })

  const { data: machines } = useQuery({
    queryKey: ['machines'],
    queryFn: () => apiHelpers.getMachines(),
  })

  const { data: images } = useQuery({
    queryKey: ['images'],
    queryFn: () => apiHelpers.getImages(),
  })

  const keepMutation = useMutation({
    mutationFn: apiHelpers.keepWriteback,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['writebacks'] })
      toast.success('Writeback kept successfully')
    },
    onError: () => {
      toast.error('Failed to keep writeback')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: apiHelpers.deleteWriteback,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['writebacks'] })
      toast.success('Writeback deleted successfully')
    },
    onError: () => {
      toast.error('Failed to delete writeback')
    },
  })

  const formatSize = (bytes: number) => {
    const units = ['B', 'KB', 'MB', 'GB', 'TB']
    let size = bytes
    let unitIndex = 0
    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024
      unitIndex++
    }
    return `${size.toFixed(2)} ${units[unitIndex]}`
  }

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString()
  }

  const handleKeep = (id: number) => {
    keepMutation.mutate(id)
  }

  const handleDelete = (id: number) => {
    if (confirm('Are you sure you want to delete this writeback?')) {
      deleteMutation.mutate(id)
    }
  }

  const totalSize = writebacks?.reduce((sum: number, w: Writeback) => sum + w.size, 0) || 0

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Writebacks</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">Manage disk image writebacks</p>
        </div>
      </div>

      {/* Statistics */}
      {writebacks && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Total Writebacks</p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">{writebacks.length || 0}</p>
                </div>
                <FileText className="h-8 w-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Total Size</p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">{formatSize(totalSize)}</p>
                </div>
                <HardDrive className="h-8 w-8 text-green-500" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Average Size</p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">
                    {writebacks.length > 0 ? formatSize(totalSize / writebacks.length) : '0 B'}
                  </p>
                </div>
                <HardDrive className="h-8 w-8 text-purple-500" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle>Filters</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Filter by Machine
              </label>
              <select
                value={selectedMachineId || ''}
                onChange={(e) => setSelectedMachineId(e.target.value ? Number(e.target.value) : undefined)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
              >
                <option value="">All Machines</option>
                {machines?.map((machine: { id: number; name: string }) => (
                  <option key={machine.id} value={machine.id}>{machine.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Filter by Image
              </label>
              <select
                value={selectedImageId || ''}
                onChange={(e) => setSelectedImageId(e.target.value ? Number(e.target.value) : undefined)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
              >
                <option value="">All Images</option>
                {images?.map((image: { id: number; name: string }) => (
                  <option key={image.id} value={image.id}>{image.name}</option>
                ))}
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Writebacks List */}
      <Card>
        <CardHeader>
          <CardTitle>Writebacks</CardTitle>
          <CardDescription>Disk image writeback files</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex justify-center py-8">
              <LoadingSpinner />
            </div>
          ) : writebacks && writebacks.length > 0 ? (
            <div className="space-y-3">
              {writebacks.map((writeback: Writeback) => (
                <div
                  key={writeback.id}
                  className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:shadow-md transition-shadow"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <FileText className="h-5 w-5 text-blue-500" />
                        <h3 className="font-semibold text-gray-900 dark:text-white">
                          {writeback.machine?.name || `Machine ${writeback.machine_id}`}
                        </h3>
                        <span className="text-sm text-gray-500 dark:text-gray-400">
                          ({writeback.image?.name || `Image ${writeback.image_id}`})
                        </span>
                      </div>
                      <div className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
                        <p className="flex items-center gap-1">
                          <HardDrive className="h-3 w-3" />
                          Size: {formatSize(writeback.size)}
                        </p>
                        <p className="font-mono text-xs text-gray-500 dark:text-gray-500 truncate">
                          {writeback.path}
                        </p>
                        <p className="text-xs text-gray-500 dark:text-gray-500">
                          Created: {formatTimestamp(writeback.created_at)}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-1 ml-4">
                      <button
                        onClick={() => handleKeep(writeback.id)}
                        disabled={keepMutation.isPending}
                        className="p-2 text-green-600 hover:bg-green-50 dark:hover:bg-green-900/20 rounded-lg transition-colors"
                        title="Keep writeback (mark as permanent)"
                      >
                        <Save className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => handleDelete(writeback.id)}
                        disabled={deleteMutation.isPending}
                        className="p-2 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                        title="Delete writeback"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500 dark:text-gray-400">
              <FileText className="h-12 w-12 mx-auto mb-4 text-gray-400" />
              <p>No writebacks found</p>
              {selectedMachineId || selectedImageId ? (
                <p className="text-sm mt-2">Try adjusting your filters</p>
              ) : (
                <p className="text-sm mt-2">Writebacks will appear here when machines create them</p>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}




