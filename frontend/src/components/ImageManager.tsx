/**
 * ImageManager Component
 * Advanced image management with conversion, validation, and storage optimization
 */

import { useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  Upload, 
  Trash2, 
  RefreshCw, 
  HardDrive, 
  AlertCircle,
  CheckCircle,
  Clock,
  Loader2,
  FileText,
  Zap,
  Eye,
  Copy
} from 'lucide-react';
import { useDropzone } from 'react-dropzone';
import { toast } from 'react-hot-toast';

import { Button } from './ui/Button';
import { Card } from './ui/Card';
import { StatusBadge } from './ui/StatusBadge';
import { ProgressBar } from './ui/ProgressBar';
// import { useAuthStore } from '../stores/authStore'; // Unused for now
import { api } from '../lib/api';

interface ImageData {
  id: number;
  name: string;
  filename: string;
  file_path: string;
  original_filename: string;
  format: 'VHDX' | 'RAW' | 'QCOW2';
  status: 'READY' | 'PROCESSING' | 'ERROR' | 'UPLOADING';
  size_bytes: number;
  virtual_size_bytes?: number;
  checksum_md5?: string;
  checksum_sha256?: string;
  image_type: 'SYSTEM' | 'APPLICATION' | 'DATA';
  description?: string;
  created_at: string;
  updated_at: string;
  created_by: number;
  error_message?: string;
  processing_log?: string;
}

interface ImageUploadProgress {
  file: File;
  progress: number;
  status: 'uploading' | 'processing' | 'completed' | 'error';
  error?: string;
}

interface ConversionJob {
  id: string;
  image_id: number;
  status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  progress: number;
  start_time: string;
  end_time?: string;
  error_message?: string;
}

const ImageManager: React.FC = () => {
  const [uploadProgress, setUploadProgress] = useState<ImageUploadProgress[]>([]);
  const [selectedImage, setSelectedImage] = useState<ImageData | null>(null);
  const [showDetails, setShowDetails] = useState(false);
  const [showUpload, setShowUpload] = useState(false);

  // const { user } = useAuthStore(); // Unused for now
  const queryClient = useQueryClient();

  // Fetch images
  const { data: imagesData, isLoading: imagesLoading, refetch: refetchImages } = useQuery({
    queryKey: ['images'],
    queryFn: () => api.get('/images/').then(res => res.data),
    refetchInterval: 5000, // Refresh every 5 seconds for processing status
  });

  // Fetch conversion jobs
  const { data: conversionJobsData } = useQuery({
    queryKey: ['conversion-jobs'],
    queryFn: () => api.get('/images/conversion-jobs').then(res => res.data),
    refetchInterval: 2000, // Refresh every 2 seconds for job progress
  });

  // Upload image mutation
  const uploadImageMutation = useMutation({
    mutationFn: async (data: FormData) => {
      const response = await api.post('/images/upload', data, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent) => {
          const progress = Math.round((progressEvent.loaded * 100) / (progressEvent.total || 1));
          // Update progress for the specific file
          setUploadProgress(prev => prev.map(item => 
            item.file === data.get('file') ? { ...item, progress } : item
          ));
        }
      });
      return response.data;
    },
    onSuccess: (data, variables) => {
      const file = variables.get('file') as File;
      setUploadProgress(prev => prev.map(item => 
        item.file === file ? { ...item, status: 'completed', progress: 100 } : item
      ));
      toast.success(`Image "${data.name}" uploaded successfully`);
      queryClient.invalidateQueries({ queryKey: ['images'] });
    },
    onError: (error: any, variables) => {
      const file = variables.get('file') as File;
      setUploadProgress(prev => prev.map(item => 
        item.file === file ? { 
          ...item, 
          status: 'error', 
          error: error.response?.data?.detail || error.message 
        } : item
      ));
      toast.error(`Failed to upload image: ${error.response?.data?.detail || error.message}`);
    },
  });

  // Delete image mutation
  const deleteImageMutation = useMutation({
    mutationFn: (id: number) => api.delete(`/images/${id}`).then(res => res.data),
    onSuccess: (data, id) => {
      toast.success(`Image ${id} deleted successfully`);
      queryClient.invalidateQueries({ queryKey: ['images'] });
    },
    onError: (error: any) => {
      toast.error(`Failed to delete image: ${error.response?.data?.detail || error.message}`);
    },
  });

  // Trigger conversion mutation
  const triggerConversionMutation = useMutation({
    mutationFn: (id: number) => api.post(`/images/${id}/convert`).then(res => res.data),
    onSuccess: (data, id) => {
      toast.success(`Conversion triggered for image ${id}`);
      queryClient.invalidateQueries({ queryKey: ['images'] });
      queryClient.invalidateQueries({ queryKey: ['conversion-jobs'] });
    },
    onError: (error: any) => {
      toast.error(`Failed to trigger conversion: ${error.response?.data?.detail || error.message}`);
    },
  });

  const images = imagesData?.images || [];
  const conversionJobs = conversionJobsData?.jobs || [];

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newUploads = acceptedFiles.map(file => ({
      file,
      progress: 0,
      status: 'uploading' as const
    }));
    
    setUploadProgress(prev => [...prev, ...newUploads]);
    
    // Upload each file
    acceptedFiles.forEach(file => {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('name', file.name.replace(/\.[^/.]+$/, ""));
      formData.append('image_type', 'SYSTEM');
      formData.append('description', `Uploaded on ${new Date().toLocaleString()}`);
      
      uploadImageMutation.mutate(formData);
    });
  }, [uploadImageMutation]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/octet-stream': ['.vhdx', '.raw', '.qcow2', '.vhd', '.img'],
      'application/x-vhd': ['.vhd', '.vhdx'],
      'application/x-raw-disk-image': ['.raw', '.img'],
      'application/x-qemu-disk': ['.qcow2']
    },
    multiple: true,
    maxSize: 10 * 1024 * 1024 * 1024, // 10GB
  });

  const handleDeleteImage = (id: number, name: string) => {
    if (window.confirm(`Are you sure you want to delete image "${name}"?`)) {
      deleteImageMutation.mutate(id);
    }
  };

  const handleTriggerConversion = (id: number) => {
    triggerConversionMutation.mutate(id);
  };

  const copyToClipboard = (text: string, label: string) => {
    navigator.clipboard.writeText(text).then(() => {
      toast.success(`${label} copied to clipboard`);
    }).catch(() => {
      toast.error('Failed to copy to clipboard');
    });
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'READY':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'PROCESSING':
        return <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />;
      case 'ERROR':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      case 'UPLOADING':
        return <Upload className="w-4 h-4 text-yellow-500" />;
      default:
        return <Clock className="w-4 h-4 text-gray-500" />;
    }
  };

  const formatFileSize = (bytes: number) => {
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    if (bytes === 0) return '0 B';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${sizes[i]}`;
  };

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const getImageTypeColor = (type: string) => {
    switch (type) {
      case 'SYSTEM':
        return 'bg-blue-100 text-blue-800';
      case 'APPLICATION':
        return 'bg-green-100 text-green-800';
      case 'DATA':
        return 'bg-purple-100 text-purple-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (imagesLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
        <span className="ml-2 text-gray-600">Loading images...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Image Management</h2>
          <p className="text-gray-600">Manage disk images for diskless boot sessions</p>
        </div>
        <div className="flex space-x-3">
          <Button
            onClick={() => refetchImages()}
            variant="outline"
            className="flex items-center space-x-2"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Refresh</span>
          </Button>
          <Button
            onClick={() => setShowUpload(!showUpload)}
            className="flex items-center space-x-2"
          >
            <Upload className="w-4 h-4" />
            <span>Upload Images</span>
          </Button>
        </div>
      </div>

      {/* Upload Area */}
      {showUpload && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Upload Images</h3>
          
          <div
            {...getRootProps()}
            className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
              isDragActive 
                ? 'border-blue-500 bg-blue-50' 
                : 'border-gray-300 hover:border-gray-400'
            }`}
          >
            <input {...getInputProps()} />
            <Upload className="w-12 h-12 mx-auto mb-4 text-gray-400" />
            {isDragActive ? (
              <p className="text-lg text-blue-600">Drop the images here...</p>
            ) : (
              <div>
                <p className="text-lg text-gray-600 mb-2">
                  Drag & drop images here, or click to select
                </p>
                <p className="text-sm text-gray-500">
                  Supports VHDX, RAW, QCOW2 formats (max 10GB each)
                </p>
              </div>
            )}
          </div>

          {/* Upload Progress */}
          {uploadProgress.length > 0 && (
            <div className="mt-4 space-y-2">
              <h4 className="font-medium text-gray-900">Upload Progress</h4>
              {uploadProgress.map((item, index) => (
                <div key={index} className="border border-gray-200 rounded-lg p-3">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-gray-900">
                      {item.file.name}
                    </span>
                    <StatusBadge status={item.status} text={item.status} />
                  </div>
                  <ProgressBar 
                    progress={item.progress} 
                    className="mb-2"
                  />
                  {item.error && (
                    <p className="text-sm text-red-600">{item.error}</p>
                  )}
                </div>
              ))}
            </div>
          )}
        </Card>
      )}

      {/* Conversion Jobs */}
      {conversionJobs.length > 0 && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Active Conversions</h3>
          <div className="space-y-3">
            {conversionJobs.map((job: ConversionJob) => (
              <div key={job.id} className="border border-gray-200 rounded-lg p-3">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium text-gray-900">
                    Image #{job.image_id} Conversion
                  </span>
                  <StatusBadge status={job.status} text={job.status} />
                </div>
                <ProgressBar progress={job.progress} />
                {job.error_message && (
                  <p className="text-sm text-red-600 mt-2">{job.error_message}</p>
                )}
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Images List */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Disk Images</h3>

        {images.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <HardDrive className="w-12 h-12 mx-auto mb-4 text-gray-300" />
            <p>No images found</p>
            <p className="text-sm">Upload your first disk image to get started</p>
          </div>
        ) : (
          <div className="space-y-4">
            {images.map((image: any) => (
              <div key={image.id} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <HardDrive className="w-5 h-5 text-blue-500" />
                      <div>
                        <h4 className="text-lg font-medium text-gray-900">
                          {image.name}
                        </h4>
                        <p className="text-sm text-gray-500">
                          {image.original_filename} • {image.format}
                        </p>
                      </div>
                      <div className="flex items-center space-x-2">
                        {getStatusIcon(image.status)}
                        <StatusBadge status={image.status} text={image.status} />
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${getImageTypeColor(image.image_type)}`}>
                          {image.image_type}
                        </span>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-3">
                      <div>
                        <p className="text-sm font-medium text-gray-700">Size</p>
                        <p className="text-sm text-gray-900">{formatFileSize(image.size_bytes)}</p>
                        {image.virtual_size_bytes && (
                          <p className="text-xs text-gray-500">
                            Virtual: {formatFileSize(image.virtual_size_bytes)}
                          </p>
                        )}
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-700">Checksums</p>
                        <div className="space-y-1">
                          {image.checksum_md5 && (
                            <div className="flex items-center space-x-2">
                              <span className="text-xs text-gray-500">MD5:</span>
                              <span className="text-xs font-mono text-gray-900">
                                {image.checksum_md5.substring(0, 8)}...
                              </span>
                              <Button
                                onClick={() => copyToClipboard(image.checksum_md5!, 'MD5 checksum')}
                                variant="outline"
                                size="sm"
                                className="p-1"
                              >
                                <Copy className="w-3 h-3" />
                              </Button>
                            </div>
                          )}
                          {image.checksum_sha256 && (
                            <div className="flex items-center space-x-2">
                              <span className="text-xs text-gray-500">SHA256:</span>
                              <span className="text-xs font-mono text-gray-900">
                                {image.checksum_sha256.substring(0, 8)}...
                              </span>
                              <Button
                                onClick={() => copyToClipboard(image.checksum_sha256!, 'SHA256 checksum')}
                                variant="outline"
                                size="sm"
                                className="p-1"
                              >
                                <Copy className="w-3 h-3" />
                              </Button>
                            </div>
                          )}
                        </div>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-700">File Path</p>
                        <div className="flex items-center space-x-2">
                          <p className="text-sm text-gray-900 font-mono truncate">
                            {image.file_path}
                          </p>
                          <Button
                            onClick={() => copyToClipboard(image.file_path, 'File path')}
                            variant="outline"
                            size="sm"
                            className="p-1"
                          >
                            <Copy className="w-3 h-3" />
                          </Button>
                        </div>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-700">Created</p>
                        <p className="text-sm text-gray-900">{formatDateTime(image.created_at)}</p>
                      </div>
                    </div>

                    {image.description && (
                      <div className="mb-3">
                        <p className="text-sm font-medium text-gray-700">Description</p>
                        <p className="text-sm text-gray-900">{image.description}</p>
                      </div>
                    )}

                    {image.error_message && (
                      <div className="mb-3 p-3 bg-red-50 border border-red-200 rounded-lg">
                        <p className="text-sm font-medium text-red-800">Error</p>
                        <p className="text-sm text-red-700">{image.error_message}</p>
                      </div>
                    )}

                    {image.processing_log && (
                      <div className="mb-3">
                        <Button
                          onClick={() => setSelectedImage(image)}
                          variant="outline"
                          size="sm"
                          className="flex items-center space-x-2"
                        >
                          <FileText className="w-4 h-4" />
                          <span>View Processing Log</span>
                        </Button>
                      </div>
                    )}
                  </div>

                  <div className="flex flex-col space-y-2 ml-4">
                    {image.status === 'READY' && image.format === 'VHDX' && (
                      <Button
                        onClick={() => handleTriggerConversion(image.id)}
                        variant="outline"
                        size="sm"
                        className="text-blue-600 hover:text-blue-700"
                      >
                        <Zap className="w-4 h-4 mr-1" />
                        Convert to RAW
                      </Button>
                    )}
                    
                    <Button
                      onClick={() => setSelectedImage(image)}
                      variant="outline"
                      size="sm"
                      className="flex items-center space-x-1"
                    >
                      <Eye className="w-4 h-4" />
                      <span>Details</span>
                    </Button>
                    
                    <Button
                      onClick={() => handleDeleteImage(image.id, image.name)}
                      variant="outline"
                      size="sm"
                      className="text-red-600 hover:text-red-700"
                    >
                      <Trash2 className="w-4 h-4 mr-1" />
                      Delete
                    </Button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Image Details Modal */}
      {selectedImage && showDetails && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">
                Image Details: {selectedImage.name}
              </h3>
              <Button
                onClick={() => setShowDetails(false)}
                variant="outline"
                size="sm"
              >
                Close
              </Button>
            </div>
            
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm font-medium text-gray-700">Format</p>
                  <p className="text-sm text-gray-900">{selectedImage.format}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-700">Status</p>
                  <div className="flex items-center space-x-2">
                    {getStatusIcon(selectedImage.status)}
                    <StatusBadge status={selectedImage.status} text={selectedImage.status} />
                  </div>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-700">Size</p>
                  <p className="text-sm text-gray-900">{formatFileSize(selectedImage.size_bytes)}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-700">Type</p>
                  <span className={`px-2 py-1 text-xs font-medium rounded-full ${getImageTypeColor(selectedImage.image_type)}`}>
                    {selectedImage.image_type}
                  </span>
                </div>
              </div>
              
              {selectedImage.processing_log && (
                <div>
                  <p className="text-sm font-medium text-gray-700 mb-2">Processing Log</p>
                  <pre className="text-xs bg-gray-100 p-3 rounded-lg overflow-x-auto">
                    {selectedImage.processing_log}
                  </pre>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ImageManager;
