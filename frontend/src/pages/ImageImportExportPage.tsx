import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiHelpers } from '../lib/api'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card'
import { LoadingSpinner } from '../components/LoadingSpinner'
import { Upload, Download, CheckCircle, Clock, AlertCircle, HardDrive } from 'lucide-react'
import toast from 'react-hot-toast'

interface DiskImage {
  id: number
  name: string
  format?: string
  size?: number
}

export default function ImageImportExportPage() {
  const [selectedImage, setSelectedImage] = useState<number | null>(null)
  const [importPath, setImportPath] = useState('')
  const [exportFormat, setExportFormat] = useState('qcow2')
  const [exportCompress, setExportCompress] = useState(false)
  const [uploadFile, setUploadFile] = useState<File | null>(null)
  const queryClient = useQueryClient()

  const { data: images, isLoading } = useQuery({
    queryKey: ['images'],
    queryFn: () => apiHelpers.getImages(),
  })

  const { data: exportStatus } = useQuery({
    queryKey: ['export-status', selectedImage],
    queryFn: () => selectedImage ? apiHelpers.getExportStatus(selectedImage) : null,
    enabled: !!selectedImage,
    refetchInterval: 2000, // Refresh every 2 seconds for active exports
  })

  const importMutation = useMutation({
    mutationFn: apiHelpers.importImage,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['images'] })
      setImportPath('')
      toast.success('Image import started successfully')
    },
    onError: () => {
      toast.error('Failed to start image import')
    },
  })

  const uploadMutation = useMutation({
    mutationFn: (formData: FormData) => apiHelpers.importImageUpload(formData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['images'] })
      setUploadFile(null)
      toast.success('Image upload started successfully')
    },
    onError: () => {
      toast.error('Failed to upload image')
    },
  })

  const exportMutation = useMutation({
    mutationFn: ({ imageId, format, compress }: { imageId: number; format: string; compress: boolean }) =>
      apiHelpers.exportImageForDownload(imageId, { format, compress }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['export-status'] })
      toast.success('Image export started successfully')
      // The export will be available for download when complete
    },
    onError: () => {
      toast.error('Failed to start image export')
    },
  })

  const handleImport = () => {
    if (!importPath.trim()) {
      toast.error('Please enter a source path')
      return
    }
    const imageName = importPath.split('/').pop() || importPath.split('\\').pop() || 'Imported Image'
    importMutation.mutate({
      name: imageName,
      source_path: importPath,
    })
  }

  const handleUpload = () => {
    if (!uploadFile) {
      toast.error('Please select a file to upload')
      return
    }
    const formData = new FormData()
    formData.append('file', uploadFile)
    formData.append('name', uploadFile.name.replace(/\.[^/.]+$/, ''))
    uploadMutation.mutate(formData)
  }

  const handleExport = () => {
    if (!selectedImage) {
      toast.error('Please select an image to export')
      return
    }
    exportMutation.mutate({
      imageId: selectedImage,
      format: exportFormat,
      compress: exportCompress,
    })
  }

  const handleDownload = async (filename: string) => {
    if (!selectedImage) return
    
    try {
      const response = await apiHelpers.downloadExportedImage(selectedImage, filename)
      const blob = new Blob([response.data])
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      toast.success('Download started')
    } catch (error) {
      toast.error('Failed to download file')
    }
  }

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

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Image Import/Export</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">Import and export disk images</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Import Section */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Upload className="h-5 w-5" />
              Import Image
            </CardTitle>
            <CardDescription>Import images from file path or upload</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Import from Path */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Import from File Path
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={importPath}
                  onChange={(e) => setImportPath(e.target.value)}
                  placeholder="/path/to/image.qcow2"
                  className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                />
                <button
                  onClick={handleImport}
                  disabled={importMutation.isPending || !importPath.trim()}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {importMutation.isPending ? 'Importing...' : 'Import'}
                </button>
              </div>
            </div>

            {/* Upload File */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Upload Image File
              </label>
              <div className="flex gap-2">
                <input
                  type="file"
                  onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                  accept=".qcow2,.vhd,.vhdx,.raw,.vmdk,.vdi"
                  className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                />
                <button
                  onClick={handleUpload}
                  disabled={uploadMutation.isPending || !uploadFile}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {uploadMutation.isPending ? 'Uploading...' : 'Upload'}
                </button>
              </div>
              {uploadFile && (
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  Selected: {uploadFile.name} ({formatSize(uploadFile.size)})
                </p>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Export Section */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Download className="h-5 w-5" />
              Export Image
            </CardTitle>
            <CardDescription>Export images to various formats</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Image Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Select Image
              </label>
              {isLoading ? (
                <LoadingSpinner />
              ) : (
                <select
                  value={selectedImage || ''}
                  onChange={(e) => setSelectedImage(e.target.value ? Number(e.target.value) : null)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                >
                  <option value="">Select an image...</option>
                  {images?.map((image: DiskImage) => (
                    <option key={image.id} value={image.id}>
                      {image.name} {image.format && `(${image.format})`}
                    </option>
                  ))}
                </select>
              )}
            </div>

            {/* Format Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Export Format
              </label>
              <select
                value={exportFormat}
                onChange={(e) => setExportFormat(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
              >
                <option value="qcow2">QCOW2</option>
                <option value="vhd">VHD</option>
                <option value="vhdx">VHDX</option>
                <option value="raw">RAW</option>
                <option value="vmdk">VMDK</option>
                <option value="vdi">VDI</option>
              </select>
            </div>

            {/* Compression Option */}
            <div className="flex items-center">
              <input
                type="checkbox"
                id="compress"
                checked={exportCompress}
                onChange={(e) => setExportCompress(e.target.checked)}
                className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <label htmlFor="compress" className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                Compress export
              </label>
            </div>

            {/* Export Button */}
            <button
              onClick={handleExport}
              disabled={exportMutation.isPending || !selectedImage}
              className="w-full px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              <Download className="h-4 w-4" />
              {exportMutation.isPending ? 'Exporting...' : 'Export Image'}
            </button>

            {/* Export Status */}
            {selectedImage && exportStatus && (
              <div className="mt-4 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  {exportStatus.status === 'completed' ? (
                    <CheckCircle className="h-4 w-4 text-green-500" />
                  ) : exportStatus.status === 'failed' ? (
                    <AlertCircle className="h-4 w-4 text-red-500" />
                  ) : (
                    <Clock className="h-4 w-4 text-blue-500 animate-spin" />
                  )}
                  <span className="font-medium text-gray-900 dark:text-white">
                    Status: {exportStatus.status}
                  </span>
                </div>
                {exportStatus.status === 'completed' && exportStatus.filename && (
                  <button
                    onClick={() => handleDownload(exportStatus.filename)}
                    className="w-full mt-2 px-3 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center justify-center gap-2"
                  >
                    <Download className="h-4 w-4" />
                    Download {exportStatus.filename}
                  </button>
                )}
                {exportStatus.progress && (
                  <div className="mt-2">
                    <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">
                      Progress: {exportStatus.progress}%
                    </div>
                    <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                      <div
                        className="bg-blue-500 h-2 rounded-full transition-all"
                        style={{ width: `${exportStatus.progress}%` }}
                      />
                    </div>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Images List */}
      <Card>
        <CardHeader>
          <CardTitle>Available Images</CardTitle>
          <CardDescription>All imported images</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex justify-center py-8">
              <LoadingSpinner />
            </div>
          ) : images && images.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {images.map((image: DiskImage) => (
                <div
                  key={image.id}
                  className={`p-4 border rounded-lg transition-all hover:shadow-md cursor-pointer ${
                    selectedImage === image.id
                      ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                      : 'border-gray-200 dark:border-gray-700'
                  }`}
                  onClick={() => setSelectedImage(image.id)}
                >
                  <div className="flex items-center gap-2 mb-2">
                    <HardDrive className="h-5 w-5 text-blue-500" />
                    <h3 className="font-semibold text-gray-900 dark:text-white">{image.name}</h3>
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">
                    {image.format && <p>Format: {image.format}</p>}
                    {image.size && <p>Size: {formatSize(image.size)}</p>}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500 dark:text-gray-400">
              <HardDrive className="h-12 w-12 mx-auto mb-4 text-gray-400" />
              <p>No images found</p>
              <p className="text-sm mt-2">Import an image to get started</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}




