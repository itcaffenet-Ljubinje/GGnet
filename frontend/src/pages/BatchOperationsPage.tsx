import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiHelpers } from '../lib/api'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card'
import { LoadingSpinner } from '../components/LoadingSpinner'
import { Layers, X, CheckCircle, XCircle, Clock, AlertCircle, HardDrive, Server, Upload, Download } from 'lucide-react'
import toast from 'react-hot-toast'

interface BatchOperation {
  id: number
  operation_type: string
  status: string
  total_items: number
  completed_items: number
  failed_items: number
  created_at: string
  started_at?: string
  completed_at?: string
  error?: string
}

export default function BatchOperationsPage() {
  const [selectedOperation, setSelectedOperation] = useState<number | null>(null)
  const [showImageModal, setShowImageModal] = useState(false)
  const [showMachineModal, setShowMachineModal] = useState(false)
  const queryClient = useQueryClient()

  const { data: operations, isLoading } = useQuery({
    queryKey: ['batch-operations'],
    queryFn: () => apiHelpers.listBatchOperations(),
    refetchInterval: 2000, // Refresh every 2 seconds for progress updates
  })

  const { data: operationDetails } = useQuery({
    queryKey: ['batch-operation', selectedOperation],
    queryFn: () => selectedOperation ? apiHelpers.getBatchOperation(selectedOperation) : null,
    enabled: !!selectedOperation,
    refetchInterval: 1000, // Refresh every second for active operations
  })

  const { data: images } = useQuery({
    queryKey: ['images'],
    queryFn: () => apiHelpers.getImages(),
  })

  const { data: machines } = useQuery({
    queryKey: ['machines'],
    queryFn: () => apiHelpers.getMachines(),
  })

  const cancelMutation = useMutation({
    mutationFn: apiHelpers.cancelBatchOperation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['batch-operations'] })
      toast.success('Operation cancelled successfully')
    },
    onError: () => {
      toast.error('Failed to cancel operation')
    },
  })

  const backupMutation = useMutation({
    mutationFn: apiHelpers.batchBackupImages,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['batch-operations'] })
      setShowImageModal(false)
      toast.success(`Batch backup started: ${data.id}`)
    },
    onError: () => {
      toast.error('Failed to start batch backup')
    },
  })

  const restoreMutation = useMutation({
    mutationFn: apiHelpers.batchRestoreImages,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['batch-operations'] })
      setShowImageModal(false)
      toast.success(`Batch restore started: ${data.id}`)
    },
    onError: () => {
      toast.error('Failed to start batch restore')
    },
  })

  const testMutation = useMutation({
    mutationFn: apiHelpers.batchTestImages,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['batch-operations'] })
      setShowImageModal(false)
      toast.success(`Batch test started: ${data.id}`)
    },
    onError: () => {
      toast.error('Failed to start batch test')
    },
  })

  const machineOpMutation = useMutation({
    mutationFn: apiHelpers.batchOperateMachines,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['batch-operations'] })
      setShowMachineModal(false)
      toast.success(`Batch operation started: ${data.id}`)
    },
    onError: () => {
      toast.error('Failed to start batch operation')
    },
  })

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-500" />
      case 'running':
      case 'in_progress':
        return <Clock className="h-4 w-4 text-blue-500 animate-spin" />
      case 'cancelled':
        return <X className="h-4 w-4 text-gray-500" />
      default:
        return <AlertCircle className="h-4 w-4 text-gray-500" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed':
        return 'bg-green-100 dark:bg-green-900/20 text-green-800 dark:text-green-300'
      case 'failed':
        return 'bg-red-100 dark:bg-red-900/20 text-red-800 dark:text-red-300'
      case 'running':
      case 'in_progress':
        return 'bg-blue-100 dark:bg-blue-900/20 text-blue-800 dark:text-blue-300'
      case 'cancelled':
        return 'bg-gray-100 dark:bg-gray-900/20 text-gray-800 dark:text-gray-300'
      default:
        return 'bg-gray-100 dark:bg-gray-900/20 text-gray-800 dark:text-gray-300'
    }
  }

  const getProgressPercentage = (operation: BatchOperation) => {
    if (operation.total_items === 0) return 0
    return Math.round((operation.completed_items / operation.total_items) * 100)
  }

  const formatTimestamp = (timestamp?: string) => {
    if (!timestamp) return 'N/A'
    return new Date(timestamp).toLocaleString()
  }

  const handleCancel = (id: number) => {
    if (confirm('Are you sure you want to cancel this operation?')) {
      cancelMutation.mutate(id)
    }
  }

  const handleImageOperation = (type: 'backup' | 'restore' | 'test', imageIds: number[], backupPath: string) => {
    const commonData = {
      image_ids: imageIds,
      backup_path: backupPath,
    }

    switch (type) {
      case 'backup':
        backupMutation.mutate(commonData)
        break
      case 'restore':
        restoreMutation.mutate(commonData)
        break
      case 'test':
        testMutation.mutate(commonData)
        break
    }
  }

  const handleMachineOperation = (operationType: string, machineIds: number[]) => {
    machineOpMutation.mutate({
      machine_ids: machineIds,
      operation_type: operationType,
    })
  }

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Batch Operations</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">Manage bulk operations on images and machines</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setShowImageModal(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
          >
            <HardDrive className="h-4 w-4" />
            Image Operations
          </button>
          <button
            onClick={() => setShowMachineModal(true)}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 flex items-center gap-2"
          >
            <Server className="h-4 w-4" />
            Machine Operations
          </button>
        </div>
      </div>

      {/* Statistics */}
      {operations && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Total Operations</p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">{operations.length || 0}</p>
                </div>
                <Layers className="h-8 w-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Running</p>
                  <p className="text-2xl font-bold text-blue-600">
                    {operations.filter((o: BatchOperation) => o.status === 'running' || o.status === 'in_progress').length}
                  </p>
                </div>
                <Clock className="h-8 w-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Completed</p>
                  <p className="text-2xl font-bold text-green-600">
                    {operations.filter((o: BatchOperation) => o.status === 'completed').length}
                  </p>
                </div>
                <CheckCircle className="h-8 w-8 text-green-500" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Failed</p>
                  <p className="text-2xl font-bold text-red-600">
                    {operations.filter((o: BatchOperation) => o.status === 'failed').length}
                  </p>
                </div>
                <XCircle className="h-8 w-8 text-red-500" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Operations List */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>Batch Operations</CardTitle>
              <CardDescription>Bulk operations on images and machines</CardDescription>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="flex justify-center py-8">
                  <LoadingSpinner />
                </div>
              ) : operations && operations.length > 0 ? (
                <div className="space-y-4">
                  {operations.map((operation: BatchOperation) => {
                    const progress = getProgressPercentage(operation)
                    const isActive = operation.status === 'running' || operation.status === 'in_progress'
                    return (
                      <div
                        key={operation.id}
                        className={`p-4 border rounded-lg transition-all hover:shadow-md ${
                          selectedOperation === operation.id
                            ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                            : 'border-gray-200 dark:border-gray-700'
                        }`}
                        onClick={() => setSelectedOperation(operation.id)}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                              <Layers className="h-5 w-5 text-blue-500" />
                              <h3 className="font-semibold text-gray-900 dark:text-white">
                                {operation.operation_type}
                              </h3>
                              <span className={`text-xs px-2 py-0.5 rounded ${getStatusColor(operation.status)}`}>
                                {operation.status}
                              </span>
                              {getStatusIcon(operation.status)}
                            </div>
                            
                            {/* Progress Bar */}
                            <div className="mb-2">
                              <div className="flex justify-between text-sm text-gray-600 dark:text-gray-400 mb-1">
                                <span>Progress: {operation.completed_items} / {operation.total_items}</span>
                                <span>{progress}%</span>
                              </div>
                              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                                <div
                                  className={`h-2 rounded-full transition-all ${
                                    operation.status === 'completed'
                                      ? 'bg-green-500'
                                      : operation.status === 'failed'
                                      ? 'bg-red-500'
                                      : 'bg-blue-500'
                                  }`}
                                  style={{ width: `${progress}%` }}
                                />
                              </div>
                            </div>

                            <div className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
                              {operation.failed_items > 0 && (
                                <p className="text-red-600 dark:text-red-400">
                                  Failed: {operation.failed_items}
                                </p>
                              )}
                              <p>Created: {formatTimestamp(operation.created_at)}</p>
                              {operation.started_at && (
                                <p>Started: {formatTimestamp(operation.started_at)}</p>
                              )}
                              {operation.completed_at && (
                                <p>Completed: {formatTimestamp(operation.completed_at)}</p>
                              )}
                            </div>
                          </div>
                          {isActive && (
                            <button
                              onClick={(e) => {
                                e.stopPropagation()
                                handleCancel(operation.id)
                              }}
                              disabled={cancelMutation.isPending}
                              className="ml-4 p-2 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                              title="Cancel operation"
                            >
                              <X className="h-4 w-4" />
                            </button>
                          )}
                        </div>
                      </div>
                    )
                  })}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                  <Layers className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                  <p>No batch operations found</p>
                  <p className="text-sm mt-2">Start a new batch operation to get started</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Operation Details */}
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle>Operation Details</CardTitle>
              <CardDescription>
                {selectedOperation ? 'Details for selected operation' : 'Select an operation to view details'}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {selectedOperation && operationDetails ? (
                <div className="space-y-4">
                  <div>
                    <h3 className="font-semibold text-gray-900 dark:text-white mb-2">General</h3>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-500 dark:text-gray-400">Type:</span>
                        <span className="text-gray-900 dark:text-white font-medium">
                          {operationDetails.operation_type}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500 dark:text-gray-400">Status:</span>
                        <span className={`px-2 py-0.5 rounded text-xs ${getStatusColor(operationDetails.status)}`}>
                          {operationDetails.status}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500 dark:text-gray-400">Progress:</span>
                        <span className="text-gray-900 dark:text-white">
                          {operationDetails.completed_items} / {operationDetails.total_items}
                        </span>
                      </div>
                      {operationDetails.failed_items > 0 && (
                        <div className="flex justify-between">
                          <span className="text-gray-500 dark:text-gray-400">Failed:</span>
                          <span className="text-red-600 dark:text-red-400">
                            {operationDetails.failed_items}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                  {operationDetails.error && (
                    <div>
                      <h3 className="font-semibold text-red-600 dark:text-red-400 mb-2">Error</h3>
                      <p className="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 p-2 rounded">
                        {operationDetails.error}
                      </p>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                  <p>Select an operation to view details</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Image Operations Modal - Placeholder */}
      {showImageModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-2xl w-full mx-4">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Batch Image Operations</h2>
            <p className="text-gray-500 dark:text-gray-400 mb-4">
              Image operation form will be implemented here. This requires image selection, operation type (backup/restore/test), and destination path.
            </p>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setShowImageModal(false)}
                className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Machine Operations Modal - Placeholder */}
      {showMachineModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-2xl w-full mx-4">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Batch Machine Operations</h2>
            <p className="text-gray-500 dark:text-gray-400 mb-4">
              Machine operation form will be implemented here. This requires machine selection and operation type (restart/shutdown/wake/turn-on).
            </p>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setShowMachineModal(false)}
                className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}




