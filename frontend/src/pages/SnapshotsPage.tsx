import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiHelpers } from '../lib/api'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card'
import { LoadingSpinner } from '../components/LoadingSpinner'
import { Camera, Trash2, Plus, Calendar, HardDrive, AlertCircle } from 'lucide-react'
import toast from 'react-hot-toast'

interface Snapshot {
  id: number
  image_id: number
  machine_id?: number
  snapshot_path: string
  description?: string
  timestamp: string
  size?: number
  image?: {
    name: string
  }
  machine?: {
    name: string
  }
}

export default function SnapshotsPage() {
  const [selectedImageId, setSelectedImageId] = useState<number | undefined>()
  const queryClient = useQueryClient()

  const { data: snapshots, isLoading } = useQuery({
    queryKey: ['snapshots', selectedImageId],
    queryFn: () => apiHelpers.getSnapshots(selectedImageId ? { image_id: selectedImageId } : undefined),
  })

  const { data: images } = useQuery({
    queryKey: ['images'],
    queryFn: () => apiHelpers.getImages(),
  })

  const { data: stats } = useQuery({
    queryKey: ['snapshot-stats'],
    queryFn: () => apiHelpers.getSnapshotStats(),
  })

  const deleteMutation = useMutation({
    mutationFn: apiHelpers.deleteSnapshot,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['snapshots'] })
      queryClient.invalidateQueries({ queryKey: ['snapshot-stats'] })
      toast.success('Snapshot deleted successfully')
    },
    onError: () => {
      toast.error('Failed to delete snapshot')
    },
  })

  const createMutation = useMutation({
    mutationFn: apiHelpers.createSnapshot,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['snapshots'] })
      queryClient.invalidateQueries({ queryKey: ['snapshot-stats'] })
      toast.success('Snapshot created successfully')
    },
    onError: () => {
      toast.error('Failed to create snapshot')
    },
  })

  const formatSize = (bytes?: number) => {
    if (!bytes) return 'Unknown'
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

  const handleCreateSnapshot = () => {
    if (!selectedImageId) {
      toast.error('Please select an image')
      return
    }
    createMutation.mutate({
      image_id: selectedImageId,
      description: `Snapshot created on ${new Date().toLocaleString()}`,
    })
  }

  const handleDeleteSnapshot = (id: number) => {
    if (confirm('Are you sure you want to delete this snapshot?')) {
      deleteMutation.mutate(id)
    }
  }

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Snapshots</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">Manage image snapshots</p>
        </div>
        <button
          onClick={handleCreateSnapshot}
          disabled={!selectedImageId || createMutation.isPending}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          <Plus className="h-4 w-4" />
          Create Snapshot
        </button>
      </div>

      {/* Statistics */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Total Snapshots</p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">{stats.total || 0}</p>
                </div>
                <Camera className="h-8 w-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Total Size</p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">{formatSize(stats.total_size)}</p>
                </div>
                <HardDrive className="h-8 w-8 text-green-500" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-500 dark:text-gray-400">By Image</p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">{stats.by_image || 0}</p>
                </div>
                <HardDrive className="h-8 w-8 text-purple-500" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Image Filter */}
      <Card>
        <CardHeader>
          <CardTitle>Filter by Image</CardTitle>
        </CardHeader>
        <CardContent>
          <select
            value={selectedImageId || ''}
            onChange={(e) => setSelectedImageId(e.target.value ? Number(e.target.value) : undefined)}
            className="w-full md:w-64 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
          >
            <option value="">All Images</option>
            {images?.map((image: { id: number; name: string }) => (
              <option key={image.id} value={image.id}>{image.name}</option>
            ))}
          </select>
        </CardContent>
      </Card>

      {/* Snapshots List */}
      <Card>
        <CardHeader>
          <CardTitle>Snapshots</CardTitle>
          <CardDescription>Image snapshots and backups</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex justify-center py-8">
              <LoadingSpinner />
            </div>
          ) : snapshots && snapshots.length > 0 ? (
            <div className="space-y-4">
              {snapshots.map((snapshot: Snapshot) => (
                <div
                  key={snapshot.id}
                  className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:shadow-md transition-shadow"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <Camera className="h-5 w-5 text-blue-500" />
                        <h3 className="font-semibold text-gray-900 dark:text-white">
                          {snapshot.image?.name || `Image ${snapshot.image_id}`}
                        </h3>
                        {snapshot.machine && (
                          <span className="text-sm text-gray-500 dark:text-gray-400">
                            (Machine: {snapshot.machine.name})
                          </span>
                        )}
                      </div>
                      {snapshot.description && (
                        <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                          {snapshot.description}
                        </p>
                      )}
                      <div className="flex items-center gap-4 text-xs text-gray-500 dark:text-gray-500">
                        <span className="flex items-center gap-1">
                          <Calendar className="h-3 w-3" />
                          {formatTimestamp(snapshot.timestamp)}
                        </span>
                        {snapshot.size && (
                          <span className="flex items-center gap-1">
                            <HardDrive className="h-3 w-3" />
                            {formatSize(snapshot.size)}
                          </span>
                        )}
                        <span className="text-xs font-mono text-gray-400 dark:text-gray-600">
                          {snapshot.snapshot_path}
                        </span>
                      </div>
                    </div>
                    <button
                      onClick={() => handleDeleteSnapshot(snapshot.id)}
                      disabled={deleteMutation.isPending}
                      className="ml-4 p-2 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors disabled:opacity-50"
                      title="Delete snapshot"
                    >
                      <Trash2 className="h-5 w-5" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500 dark:text-gray-400">
              <AlertCircle className="h-12 w-12 mx-auto mb-4 text-gray-400" />
              <p>No snapshots found</p>
              {selectedImageId && (
                <p className="text-sm mt-2">Try selecting a different image or create a new snapshot</p>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}




