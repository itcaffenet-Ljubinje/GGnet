import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import {
  Upload,
  HardDrive,
  Download,
  Trash2,
  Edit,
  Eye,
  Plus,
  Search,
  Filter,
} from 'lucide-react'
import { useDropzone } from 'react-dropzone'
import { apiHelpers } from '../lib/api'
import toast from 'react-hot-toast'
import { clsx } from 'clsx'

interface Image {
  id: number
  name: string
  description?: string
  filename: string
  format: string
  size_bytes: number
  status: string
  image_type: string
  created_at: string
  created_by_username: string
}

function ImageUploadModal({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
  const [uploadProgress, setUploadProgress] = useState(0)
  const [isUploading, setIsUploading] = useState(false)
  const queryClient = useQueryClient()

  const uploadMutation = useMutation(
    (formData: FormData) => apiHelpers.uploadImage(formData, setUploadProgress),
    {
      onSuccess: () => {
        toast.success('Image uploaded successfully')
        queryClient.invalidateQueries('images')
        onClose()
        setUploadProgress(0)
      },
      onError: (error: any) => {
        toast.error(error.response?.data?.detail || 'Upload failed')
      },
      onSettled: () => {
        setIsUploading(false)
      },
    }
  )

  const onDrop = (acceptedFiles: File[]) => {
    const file = acceptedFiles[0]
    if (!file) return

    const formData = new FormData()
    formData.append('file', file)
    formData.append('name', file.name.replace(/\.[^/.]+$/, ''))
    formData.append('image_type', 'system')

    setIsUploading(true)
    uploadMutation.mutate(formData)
  }

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/octet-stream': ['.vhd', '.vhdx', '.raw', '.qcow2', '.vmdk', '.vdi'],
    },
    maxFiles: 1,
    disabled: isUploading,
  })

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
        <div className="mt-3">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Upload Disk Image</h3>
          
          <div
            {...getRootProps()}
            className={clsx(
              'border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors',
              isDragActive
                ? 'border-primary-500 bg-primary-50'
                : 'border-gray-300 hover:border-gray-400',
              isUploading && 'pointer-events-none opacity-50'
            )}
          >
            <input {...getInputProps()} />
            <Upload className="mx-auto h-12 w-12 text-gray-400" />
            <p className="mt-2 text-sm text-gray-600">
              {isDragActive
                ? 'Drop the image file here...'
                : 'Drag & drop an image file here, or click to select'}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              Supported formats: VHD, VHDX, RAW, QCOW2, VMDK, VDI
            </p>
          </div>

          {isUploading && (
            <div className="mt-4">
              <div className="flex items-center justify-between text-sm text-gray-600 mb-1">
                <span>Uploading...</span>
                <span>{uploadProgress}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            </div>
          )}

          <div className="flex justify-end space-x-3 mt-6">
            <button
              onClick={onClose}
              disabled={isUploading}
              className="btn btn-secondary btn-md"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

function ImageCard({ image }: { image: Image }) {
  const queryClient = useQueryClient()

  const deleteMutation = useMutation(
    (id: number) => apiHelpers.deleteImage(id),
    {
      onSuccess: () => {
        toast.success('Image deleted successfully')
        queryClient.invalidateQueries('images')
      },
      onError: (error: any) => {
        toast.error(error.response?.data?.detail || 'Delete failed')
      },
    }
  )

  const handleDelete = () => {
    if (window.confirm(`Are you sure you want to delete "${image.name}"?`)) {
      deleteMutation.mutate(image.id)
    }
  }

  const formatFileSize = (bytes: number) => {
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
    if (bytes === 0) return '0 Bytes'
    const i = Math.floor(Math.log(bytes) / Math.log(1024))
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i]
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ready':
        return 'badge-success'
      case 'uploading':
      case 'processing':
        return 'badge-warning'
      case 'error':
        return 'badge-error'
      default:
        return 'badge-secondary'
    }
  }

  return (
    <div className="card">
      <div className="card-content">
        <div className="flex items-start justify-between">
          <div className="flex items-start space-x-3">
            <div className="flex-shrink-0">
              <HardDrive className="h-8 w-8 text-gray-400" />
            </div>
            <div className="min-w-0 flex-1">
              <h3 className="text-sm font-medium text-gray-900 truncate">
                {image.name}
              </h3>
              <p className="text-sm text-gray-500 truncate">
                {image.description || 'No description'}
              </p>
              <div className="mt-2 flex items-center space-x-4 text-xs text-gray-500">
                <span>{formatFileSize(image.size_bytes)}</span>
                <span className="uppercase">{image.format}</span>
                <span className="capitalize">{image.image_type}</span>
              </div>
              <div className="mt-1 flex items-center space-x-2">
                <span className={`badge ${getStatusColor(image.status)}`}>
                  {image.status}
                </span>
                <span className="text-xs text-gray-500">
                  by {image.created_by_username}
                </span>
              </div>
            </div>
          </div>
          
          <div className="flex items-center space-x-1">
            <button
              className="p-1 text-gray-400 hover:text-gray-600"
              title="View details"
            >
              <Eye className="h-4 w-4" />
            </button>
            <button
              className="p-1 text-gray-400 hover:text-gray-600"
              title="Edit"
            >
              <Edit className="h-4 w-4" />
            </button>
            <button
              onClick={handleDelete}
              disabled={deleteMutation.isLoading}
              className="p-1 text-gray-400 hover:text-red-600"
              title="Delete"
            >
              <Trash2 className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default function ImagesPage() {
  const [showUploadModal, setShowUploadModal] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [filterStatus, setFilterStatus] = useState('')

  const { data: imagesData, isLoading, error } = useQuery(
    ['images', searchTerm, filterStatus],
    () => apiHelpers.getImages({
      search: searchTerm || undefined,
      status: filterStatus || undefined,
    }),
    {
      refetchInterval: 10000, // Refresh every 10 seconds
    }
  )

  const images = imagesData?.data || []

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Disk Images</h1>
          <p className="mt-1 text-sm text-gray-500">
            Manage VHD, VHDX, and other disk image files for diskless boot
          </p>
        </div>
        <button
          onClick={() => setShowUploadModal(true)}
          className="btn btn-primary btn-md"
        >
          <Plus className="h-4 w-4 mr-2" />
          Upload Image
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="flex-1">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search images..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="input pl-10"
            />
          </div>
        </div>
        <div className="sm:w-48">
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="input"
          >
            <option value="">All Status</option>
            <option value="ready">Ready</option>
            <option value="uploading">Uploading</option>
            <option value="processing">Processing</option>
            <option value="error">Error</option>
          </select>
        </div>
      </div>

      {/* Content */}
      {isLoading ? (
        <div className="flex justify-center items-center h-64">
          <div className="spinner h-8 w-8" />
        </div>
      ) : error ? (
        <div className="text-center py-12">
          <p className="text-gray-500">Failed to load images</p>
        </div>
      ) : images.length === 0 ? (
        <div className="text-center py-12">
          <HardDrive className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No images</h3>
          <p className="mt-1 text-sm text-gray-500">
            Get started by uploading your first disk image.
          </p>
          <div className="mt-6">
            <button
              onClick={() => setShowUploadModal(true)}
              className="btn btn-primary btn-md"
            >
              <Plus className="h-4 w-4 mr-2" />
              Upload Image
            </button>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {images.map((image: Image) => (
            <ImageCard key={image.id} image={image} />
          ))}
        </div>
      )}

      {/* Upload Modal */}
      <ImageUploadModal
        isOpen={showUploadModal}
        onClose={() => setShowUploadModal(false)}
      />
    </div>
  )
}

