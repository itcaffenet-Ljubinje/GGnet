import { useState, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Upload,
  HardDrive,
  Trash2,
  Edit,
  Eye,
  Plus,
  Search,
  Filter,
  Download,
  RefreshCw,
  MoreVertical,
  CheckCircle,
  Clock,
  AlertCircle,
  FileImage,
  Calendar,
  User
} from 'lucide-react'
import { useDropzone } from 'react-dropzone'
import { apiHelpers } from '../lib/api'
import toast from 'react-hot-toast'
import { clsx } from 'clsx'
import { Card, CardHeader, CardTitle, CardContent, Button, Input, Modal, ConfirmModal } from '../components/ui'
import { LoadingSpinner } from '../components/LoadingSpinner'

interface Image {
  id: number
  name: string
  description?: string
  filename: string
  format: string
  size_bytes: number
  virtual_size_bytes?: number
  status: string
  image_type: string
  checksum_md5?: string
  checksum_sha256?: string
  created_at: string
  created_by_username: string
}

interface ImageFilters {
  status: string
  format: string
  image_type: string
  search: string
}

function ImageUploadModal({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
  const [uploadProgress, setUploadProgress] = useState(0)
  const [isUploading, setIsUploading] = useState(false)
  const [imageName, setImageName] = useState('')
  const [imageDescription, setImageDescription] = useState('')
  const [imageType, setImageType] = useState('system')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const queryClient = useQueryClient()

  const uploadMutation = useMutation({
    mutationFn: (formData: FormData) => apiHelpers.uploadImage(formData, setUploadProgress),
    onSuccess: () => {
      toast.success('Image uploaded successfully')
      queryClient.invalidateQueries({ queryKey: ['images'] })
      onClose()
      resetForm()
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Upload failed')
    },
    onSettled: () => {
      setIsUploading(false)
    },
  })

  const resetForm = () => {
    setUploadProgress(0)
    setImageName('')
    setImageDescription('')
    setImageType('system')
    setSelectedFile(null)
  }

  const onDrop = (acceptedFiles: File[]) => {
    const file = acceptedFiles[0]
    if (!file) return

    setSelectedFile(file)
    if (!imageName) {
      setImageName(file.name.replace(/\.[^/.]+$/, ''))
    }
  }

  const handleUpload = () => {
    if (!selectedFile) return

    const formData = new FormData()
    formData.append('file', selectedFile)
    formData.append('name', imageName)
    formData.append('description', imageDescription)
    formData.append('image_type', imageType)

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

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="lg" title="Upload Disk Image">
      <div className="space-y-6">
        {/* File Drop Zone */}
          <div
            {...getRootProps()}
            className={clsx(
            'border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors',
              isDragActive
              ? 'border-blue-500 bg-blue-50'
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

        {/* Selected File Info */}
        {selectedFile && (
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center">
              <FileImage className="h-8 w-8 text-blue-500 mr-3" />
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-900">{selectedFile.name}</p>
                <p className="text-xs text-gray-500">{formatFileSize(selectedFile.size)}</p>
              </div>
            </div>
          </div>
        )}

        {/* Upload Progress */}
          {isUploading && (
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
                <span>Uploading...</span>
                <span>{uploadProgress}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            </div>
          )}

        {/* Form Fields */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Input
            label="Image Name"
            value={imageName}
            onChange={(e) => setImageName(e.target.value)}
            placeholder="Enter image name"
            disabled={isUploading}
          />
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Image Type
            </label>
            <select
              value={imageType}
              onChange={(e) => setImageType(e.target.value)}
              disabled={isUploading}
              className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="system">System Image</option>
              <option value="game">Game Image</option>
              <option value="utility">Utility Image</option>
            </select>
          </div>
        </div>

        <Input
          label="Description"
          value={imageDescription}
          onChange={(e) => setImageDescription(e.target.value)}
          placeholder="Enter image description (optional)"
          disabled={isUploading}
        />

        {/* Actions */}
        <div className="flex justify-end space-x-3">
          <Button
            variant="outline"
            onClick={onClose}
            disabled={isUploading}
          >
            Cancel
          </Button>
          <Button
            onClick={handleUpload}
            disabled={!selectedFile || !imageName || isUploading}
            isLoading={isUploading}
            leftIcon={<Upload className="h-4 w-4" />}
          >
            Upload Image
          </Button>
        </div>
      </div>
    </Modal>
  )
}

function ImageCard({ image, onEdit, onDelete, onView }: {
  image: Image
  onEdit: (image: Image) => void
  onDelete: (image: Image) => void
  onView: (image: Image) => void
}) {
  const [showActions, setShowActions] = useState(false)

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'ready':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'processing':
        return <Clock className="h-4 w-4 text-yellow-500" />
      case 'error':
        return <AlertCircle className="h-4 w-4 text-red-500" />
      default:
        return <Clock className="h-4 w-4 text-gray-500" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ready':
        return 'bg-green-100 text-green-800'
      case 'processing':
        return 'bg-yellow-100 text-yellow-800'
      case 'error':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  return (
    <Card className="hover:shadow-lg transition-shadow duration-200">
      <CardContent className="p-6">
        <div className="flex items-start justify-between">
          <div className="flex items-start space-x-3 flex-1">
            <div className="flex-shrink-0">
              <div className="h-12 w-12 bg-blue-100 rounded-lg flex items-center justify-center">
                <HardDrive className="h-6 w-6 text-blue-600" />
              </div>
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="text-lg font-semibold text-gray-900 truncate">
                {image.name}
              </h3>
              {image.description && (
                <p className="text-sm text-gray-600 mt-1 line-clamp-2">
                  {image.description}
                </p>
              )}
              <div className="flex items-center mt-2 space-x-4 text-xs text-gray-500">
                <span className="flex items-center">
                  <FileImage className="h-3 w-3 mr-1" />
                  {image.format.toUpperCase()}
                </span>
                <span>{formatFileSize(image.size_bytes)}</span>
                <span className="capitalize">{image.image_type}</span>
              </div>
              <div className="flex items-center mt-2 space-x-4 text-xs text-gray-500">
                <span className="flex items-center">
                  <User className="h-3 w-3 mr-1" />
                  {image.created_by_username}
                </span>
                <span className="flex items-center">
                  <Calendar className="h-3 w-3 mr-1" />
                  {new Date(image.created_at).toLocaleDateString()}
                </span>
              </div>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <span className={clsx(
              'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
              getStatusColor(image.status)
            )}>
              {getStatusIcon(image.status)}
              <span className="ml-1 capitalize">{image.status}</span>
            </span>
            
            <div className="relative">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowActions(!showActions)}
              >
                <MoreVertical className="h-4 w-4" />
              </Button>
              
              {showActions && (
                <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg z-10 border border-gray-200">
                  <div className="py-1">
            <button
                      onClick={() => {
                        onView(image)
                        setShowActions(false)
                      }}
                      className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    >
                      <Eye className="h-4 w-4 mr-2" />
                      View Details
            </button>
            <button
                      onClick={() => {
                        onEdit(image)
                        setShowActions(false)
                      }}
                      className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    >
                      <Edit className="h-4 w-4 mr-2" />
                      Edit
            </button>
            <button
                      onClick={() => {
                        onDelete(image)
                        setShowActions(false)
                      }}
                      className="flex items-center w-full px-4 py-2 text-sm text-red-700 hover:bg-red-50"
                    >
                      <Trash2 className="h-4 w-4 mr-2" />
                      Delete
            </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

export default function ImagesPage() {
  const [showUploadModal, setShowUploadModal] = useState(false)
  const [showDeleteModal, setShowDeleteModal] = useState(false)
  const [selectedImage, setSelectedImage] = useState<Image | null>(null)
  const [filters, setFilters] = useState<ImageFilters>({
    status: '',
    format: '',
    image_type: '',
    search: ''
  })
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')
  
  const queryClient = useQueryClient()

  // Fetch images
  const { data: images = [], isLoading, error } = useQuery({
    queryKey: ['images'],
    queryFn: () => apiHelpers.getImages(),
  })

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (id: number) => apiHelpers.deleteImage(id),
    onSuccess: () => {
      toast.success('Image deleted successfully')
      queryClient.invalidateQueries({ queryKey: ['images'] })
      setShowDeleteModal(false)
      setSelectedImage(null)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Delete failed')
    },
  })

  // Filter images
  const filteredImages = useMemo(() => {
    return images.filter((image: Image) => {
      const matchesSearch = !filters.search || 
        image.name.toLowerCase().includes(filters.search.toLowerCase()) ||
        image.description?.toLowerCase().includes(filters.search.toLowerCase())
      
      const matchesStatus = !filters.status || image.status === filters.status
      const matchesFormat = !filters.format || image.format === filters.format
      const matchesType = !filters.image_type || image.image_type === filters.image_type

      return matchesSearch && matchesStatus && matchesFormat && matchesType
    })
  }, [images, filters])

  const handleDelete = (image: Image) => {
    setSelectedImage(image)
    setShowDeleteModal(true)
  }

  const confirmDelete = () => {
    if (selectedImage) {
      deleteMutation.mutate(selectedImage.id)
    }
  }

  const handleEdit = (image: Image) => {
    // TODO: Implement edit functionality
    toast.info('Edit functionality coming soon')
  }

  const handleView = (image: Image) => {
    // TODO: Implement view functionality
    toast.info('View functionality coming soon')
  }

  if (isLoading) {
    return <LoadingSpinner size="lg" text="Loading images..." />
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">Failed to load images</h3>
        <p className="text-gray-600 mb-4">There was an error loading the images.</p>
        <Button onClick={() => window.location.reload()}>
          Try Again
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Disk Images</h1>
          <p className="mt-1 text-sm text-gray-500">
            Manage your disk images for diskless boot sessions
          </p>
        </div>
        <Button
          onClick={() => setShowUploadModal(true)}
          leftIcon={<Plus className="h-4 w-4" />}
        >
          Upload Image
        </Button>
      </div>

      {/* Filters and Search */}
      <Card>
        <CardContent className="p-6">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
            <Input
              placeholder="Search images..."
              value={filters.search}
              onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
              leftIcon={<Search className="h-4 w-4" />}
            />
            
          <select
              value={filters.status}
              onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">All Status</option>
            <option value="ready">Ready</option>
            <option value="processing">Processing</option>
            <option value="error">Error</option>
          </select>
            
            <select
              value={filters.format}
              onChange={(e) => setFilters(prev => ({ ...prev, format: e.target.value }))}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">All Formats</option>
              <option value="vhd">VHD</option>
              <option value="vhdx">VHDX</option>
              <option value="raw">RAW</option>
              <option value="qcow2">QCOW2</option>
            </select>
            
            <select
              value={filters.image_type}
              onChange={(e) => setFilters(prev => ({ ...prev, image_type: e.target.value }))}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">All Types</option>
              <option value="system">System</option>
              <option value="game">Game</option>
              <option value="utility">Utility</option>
            </select>
            
            <div className="flex space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setFilters({ status: '', format: '', image_type: '', search: '' })}
              >
                Clear
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => window.location.reload()}
                leftIcon={<RefreshCw className="h-4 w-4" />}
              >
                Refresh
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Results Summary */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-gray-700">
          Showing {filteredImages.length} of {images.length} images
        </p>
        <div className="flex items-center space-x-2">
          <Button
            variant={viewMode === 'grid' ? 'primary' : 'outline'}
            size="sm"
            onClick={() => setViewMode('grid')}
          >
            Grid
          </Button>
          <Button
            variant={viewMode === 'list' ? 'primary' : 'outline'}
            size="sm"
            onClick={() => setViewMode('list')}
          >
            List
          </Button>
        </div>
      </div>

      {/* Images Grid/List */}
      {filteredImages.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center">
            <HardDrive className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No images found</h3>
            <p className="text-gray-600 mb-4">
              {filters.search || filters.status || filters.format || filters.image_type
                ? 'Try adjusting your filters to see more results.'
                : 'Get started by uploading your first disk image.'}
            </p>
            <Button
              onClick={() => setShowUploadModal(true)}
              leftIcon={<Plus className="h-4 w-4" />}
            >
              Upload Image
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className={clsx(
          viewMode === 'grid'
            ? 'grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3'
            : 'space-y-4'
        )}>
          {filteredImages.map((image: Image) => (
            <ImageCard
              key={image.id}
              image={image}
              onEdit={handleEdit}
              onDelete={handleDelete}
              onView={handleView}
            />
          ))}
        </div>
      )}

      {/* Upload Modal */}
      <ImageUploadModal
        isOpen={showUploadModal}
        onClose={() => setShowUploadModal(false)}
      />

      {/* Delete Confirmation Modal */}
      <ConfirmModal
        isOpen={showDeleteModal}
        onClose={() => setShowDeleteModal(false)}
        onConfirm={confirmDelete}
        title="Delete Image"
        message={`Are you sure you want to delete "${selectedImage?.name}"? This action cannot be undone.`}
        confirmText="Delete"
        cancelText="Cancel"
        variant="danger"
        isLoading={deleteMutation.isPending}
      />
    </div>
  )
}