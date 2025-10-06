import React, { useState, useCallback, useRef } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, X, File, CheckCircle, AlertCircle, Clock } from 'lucide-react'
import { Button } from './ui'
import { useNotifications } from './notifications'
import { apiHelpers } from '../lib/api'

interface UploadFile {
  id: string
  file: File
  progress: number
  status: 'uploading' | 'completed' | 'error' | 'converting'
  error?: string
  response?: any
}

interface FileUploadProps {
  onUploadComplete?: (files: any[]) => void
  maxFiles?: number
  acceptedTypes?: string[]
  maxSize?: number
}

export function FileUpload({ 
  onUploadComplete, 
  maxFiles = 10, 
  acceptedTypes = ['.vhd', '.vhdx', '.iso', '.img', '.raw', '.qcow2'],
  maxSize = 50 * 1024 * 1024 * 1024 // 50GB
}: FileUploadProps) {
  const [files, setFiles] = useState<UploadFile[]>([])
  const [isUploading, setIsUploading] = useState(false)
  const { addNotification } = useNotifications()
  const abortControllerRef = useRef<AbortController | null>(null)

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newFiles: UploadFile[] = acceptedFiles.map(file => ({
      id: Math.random().toString(36).substr(2, 9),
      file,
      progress: 0,
      status: 'uploading' as const
    }))

    setFiles(prev => [...prev, ...newFiles])
    uploadFiles(newFiles)
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: acceptedTypes.reduce((acc, type) => {
      acc[type] = []
      return acc
    }, {} as Record<string, string[]>),
    maxFiles,
    maxSize
  })

  const uploadFiles = async (filesToUpload: UploadFile[]) => {
    setIsUploading(true)
    abortControllerRef.current = new AbortController()

    try {
      for (const fileItem of filesToUpload) {
        await uploadSingleFile(fileItem)
      }
    } catch (error) {
      console.error('Upload error:', error)
    } finally {
      setIsUploading(false)
    }
  }

  const uploadSingleFile = async (fileItem: UploadFile) => {
    const formData = new FormData()
    formData.append('file', fileItem.file)
    formData.append('name', fileItem.file.name.replace(/\.[^/.]+$/, ''))
    formData.append('description', `Uploaded ${fileItem.file.name}`)
    formData.append('format', 'VHD')

    try {
      // Update file status
      setFiles(prev => prev.map(f => 
        f.id === fileItem.id ? { ...f, status: 'uploading' } : f
      ))

      const response = await apiHelpers.uploadImage(formData, abortControllerRef.current?.signal)
      
      // Update file status to completed
      setFiles(prev => prev.map(f => 
        f.id === fileItem.id 
          ? { ...f, status: 'completed', progress: 100, response } 
          : f
      ))

      addNotification({
        type: 'success',
        message: `Successfully uploaded ${fileItem.file.name}`
      })

      if (onUploadComplete) {
        onUploadComplete([response])
      }

    } catch (error: any) {
      // Update file status to error
      setFiles(prev => prev.map(f => 
        f.id === fileItem.id 
          ? { ...f, status: 'error', error: error.message } 
          : f
      ))

      addNotification({
        type: 'error',
        message: `Failed to upload ${fileItem.file.name}: ${error.message}`
      })
    }
  }

  const removeFile = (fileId: string) => {
    setFiles(prev => prev.filter(f => f.id !== fileId))
  }

  const cancelUpload = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
      setIsUploading(false)
      setFiles(prev => prev.map(f => 
        f.status === 'uploading' ? { ...f, status: 'error', error: 'Upload cancelled' } : f
      ))
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const getStatusIcon = (status: UploadFile['status']) => {
    switch (status) {
      case 'uploading':
        return <Clock className="h-4 w-4 text-blue-500 animate-spin" />
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'error':
        return <AlertCircle className="h-4 w-4 text-red-500" />
      case 'converting':
        return <Clock className="h-4 w-4 text-yellow-500 animate-pulse" />
      default:
        return <File className="h-4 w-4 text-gray-500" />
    }
  }

  const getStatusColor = (status: UploadFile['status']) => {
    switch (status) {
      case 'uploading':
        return 'border-blue-200 bg-blue-50'
      case 'completed':
        return 'border-green-200 bg-green-50'
      case 'error':
        return 'border-red-200 bg-red-50'
      case 'converting':
        return 'border-yellow-200 bg-yellow-50'
      default:
        return 'border-gray-200 bg-gray-50'
    }
  }

  return (
    <div className="space-y-4">
      {/* Drop Zone */}
      <div
        {...getRootProps()}
        className={`
          border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
          ${isDragActive 
            ? 'border-blue-400 bg-blue-50' 
            : 'border-gray-300 hover:border-gray-400'
          }
          ${isUploading ? 'pointer-events-none opacity-50' : ''}
        `}
      >
        <input {...getInputProps()} />
        <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
        {isDragActive ? (
          <p className="text-lg text-blue-600">Drop the files here...</p>
        ) : (
          <div>
            <p className="text-lg text-gray-600 mb-2">
              Drag & drop image files here, or click to select
            </p>
            <p className="text-sm text-gray-500">
              Supported formats: {acceptedTypes.join(', ')}
            </p>
            <p className="text-sm text-gray-500">
              Max file size: {formatFileSize(maxSize)}
            </p>
          </div>
        )}
      </div>

      {/* File List */}
      {files.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">
              Upload Progress
            </h3>
            {isUploading && (
              <Button 
                variant="outline" 
                size="sm" 
                onClick={cancelUpload}
                className="text-red-600 hover:text-red-700"
              >
                Cancel Upload
              </Button>
            )}
          </div>
          
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {files.map((fileItem) => (
              <div
                key={fileItem.id}
                className={`
                  flex items-center justify-between p-3 rounded-lg border
                  ${getStatusColor(fileItem.status)}
                `}
              >
                <div className="flex items-center space-x-3 flex-1 min-w-0">
                  {getStatusIcon(fileItem.status)}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {fileItem.file.name}
                    </p>
                    <p className="text-xs text-gray-500">
                      {formatFileSize(fileItem.file.size)}
                    </p>
                    {fileItem.status === 'uploading' && (
                      <div className="w-full bg-gray-200 rounded-full h-1.5 mt-1">
                        <div
                          className="bg-blue-600 h-1.5 rounded-full transition-all duration-300"
                          style={{ width: `${fileItem.progress}%` }}
                        />
                      </div>
                    )}
                    {fileItem.error && (
                      <p className="text-xs text-red-600 mt-1">{fileItem.error}</p>
                    )}
                  </div>
                </div>
                
                <button
                  onClick={() => removeFile(fileItem.id)}
                  className="ml-2 p-1 text-gray-400 hover:text-gray-600 transition-colors"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Upload Summary */}
      {files.length > 0 && (
        <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
            <div>
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                {files.length}
              </p>
              <p className="text-sm text-gray-500">Total Files</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-green-600">
                {files.filter(f => f.status === 'completed').length}
              </p>
              <p className="text-sm text-gray-500">Completed</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-blue-600">
                {files.filter(f => f.status === 'uploading').length}
              </p>
              <p className="text-sm text-gray-500">Uploading</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-red-600">
                {files.filter(f => f.status === 'error').length}
              </p>
              <p className="text-sm text-gray-500">Errors</p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
