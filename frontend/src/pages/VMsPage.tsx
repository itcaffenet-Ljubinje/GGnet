import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiHelpers } from '../lib/api'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card'
import { LoadingSpinner } from '../components/LoadingSpinner'
import { Server, Play, Square, Trash2, Plus, Power, Monitor, Cpu, HardDrive, AlertCircle, CheckCircle, XCircle } from 'lucide-react'
import toast from 'react-hot-toast'

interface VM {
  id: number
  name: string
  vm_id: string
  image_id: number
  status: string
  vcpus: number
  ram_mb: number
  disk_path?: string
  zfs_clone?: string
  mac_address?: string
  ip_address?: string
  vnc_port?: number
  vnc_token?: string
  boot_mode?: string
  image?: {
    name: string
  }
}

export default function VMsPage() {
  const [selectedVM, setSelectedVM] = useState<number | null>(null)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const queryClient = useQueryClient()

  const { data: vms, isLoading } = useQuery({
    queryKey: ['vms'],
    queryFn: () => apiHelpers.getVMs(),
  })

  const { data: images } = useQuery({
    queryKey: ['images'],
    queryFn: () => apiHelpers.getImages(),
  })

  const { data: vmDetails } = useQuery({
    queryKey: ['vm', selectedVM],
    queryFn: () => selectedVM ? apiHelpers.getVM(selectedVM) : null,
    enabled: !!selectedVM,
  })

  const startMutation = useMutation({
    mutationFn: apiHelpers.startVM,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vms'] })
      toast.success('VM started successfully')
    },
    onError: () => {
      toast.error('Failed to start VM')
    },
  })

  const stopMutation = useMutation({
    mutationFn: apiHelpers.stopVM,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vms'] })
      toast.success('VM stopped successfully')
    },
    onError: () => {
      toast.error('Failed to stop VM')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: apiHelpers.deleteVM,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vms'] })
      setSelectedVM(null)
      toast.success('VM deleted successfully')
    },
    onError: () => {
      toast.error('Failed to delete VM')
    },
  })

  const vncMutation = useMutation({
    mutationFn: apiHelpers.getVMVNC,
    onSuccess: (data) => {
      if (data.vnc_url) {
        window.open(data.vnc_url, '_blank')
      } else {
        toast.error('VNC URL not available')
      }
    },
    onError: () => {
      toast.error('Failed to get VNC URL')
    },
  })

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'running':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'stopped':
      case 'shutoff':
        return <XCircle className="h-4 w-4 text-gray-500" />
      case 'paused':
        return <AlertCircle className="h-4 w-4 text-yellow-500" />
      default:
        return <AlertCircle className="h-4 w-4 text-gray-500" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'running':
        return 'bg-green-100 dark:bg-green-900/20 text-green-800 dark:text-green-300'
      case 'stopped':
      case 'shutoff':
        return 'bg-gray-100 dark:bg-gray-900/20 text-gray-800 dark:text-gray-300'
      case 'paused':
        return 'bg-yellow-100 dark:bg-yellow-900/20 text-yellow-800 dark:text-yellow-300'
      default:
        return 'bg-gray-100 dark:bg-gray-900/20 text-gray-800 dark:text-gray-300'
    }
  }

  const formatMemory = (mb: number) => {
    if (mb >= 1024) {
      return `${(mb / 1024).toFixed(2)} GB`
    }
    return `${mb} MB`
  }

  const handleStart = (id: number) => {
    startMutation.mutate(id)
  }

  const handleStop = (id: number) => {
    if (confirm('Are you sure you want to stop this VM?')) {
      stopMutation.mutate(id)
    }
  }

  const handleDelete = (id: number) => {
    if (confirm('Are you sure you want to delete this VM? This action cannot be undone.')) {
      deleteMutation.mutate(id)
    }
  }

  const handleVNC = (id: number) => {
    vncMutation.mutate(id)
  }

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Virtual Machines</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">Manage QEMU/KVM virtual machines</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
        >
          <Plus className="h-4 w-4" />
          Create VM
        </button>
      </div>

      {/* Statistics */}
      {vms && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Total VMs</p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">{vms.length || 0}</p>
                </div>
                <Server className="h-8 w-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Running</p>
                  <p className="text-2xl font-bold text-green-600">
                    {vms.filter((v: VM) => v.status === 'running').length}
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
                  <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Stopped</p>
                  <p className="text-2xl font-bold text-gray-600">
                    {vms.filter((v: VM) => v.status === 'stopped' || v.status === 'shutoff').length}
                  </p>
                </div>
                <XCircle className="h-8 w-8 text-gray-500" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Total CPU</p>
                  <p className="text-2xl font-bold text-purple-600">
                    {vms.reduce((sum: number, v: VM) => sum + (v.vcpus || 0), 0)}
                  </p>
                </div>
                <Cpu className="h-8 w-8 text-purple-500" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* VMs List */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>Virtual Machines</CardTitle>
              <CardDescription>QEMU/KVM virtual machine instances</CardDescription>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="flex justify-center py-8">
                  <LoadingSpinner />
                </div>
              ) : vms && vms.length > 0 ? (
                <div className="space-y-3">
                  {vms.map((vm: VM) => (
                    <div
                      key={vm.id}
                      className={`p-4 border rounded-lg transition-all hover:shadow-md ${
                        selectedVM === vm.id
                          ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                          : 'border-gray-200 dark:border-gray-700'
                      }`}
                      onClick={() => setSelectedVM(vm.id)}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <Server className="h-5 w-5 text-blue-500" />
                            <h3 className="font-semibold text-gray-900 dark:text-white">{vm.name}</h3>
                            <span className={`text-xs px-2 py-0.5 rounded ${getStatusColor(vm.status)}`}>
                              {vm.status}
                            </span>
                            {getStatusIcon(vm.status)}
                          </div>
                          <div className="grid grid-cols-2 gap-2 text-sm text-gray-600 dark:text-gray-400">
                            <div className="flex items-center gap-1">
                              <Cpu className="h-4 w-4" />
                              <span>{vm.vcpus} vCPU{vm.vcpus !== 1 ? 's' : ''}</span>
                            </div>
                            <div className="flex items-center gap-1">
                              <HardDrive className="h-4 w-4" />
                              <span>{formatMemory(vm.ram_mb)}</span>
                            </div>
                            {vm.image && (
                              <div className="flex items-center gap-1">
                                <Monitor className="h-4 w-4" />
                                <span>{vm.image.name}</span>
                              </div>
                            )}
                            {vm.ip_address && (
                              <div className="flex items-center gap-1">
                                <Power className="h-4 w-4" />
                                <span>{vm.ip_address}</span>
                              </div>
                            )}
                          </div>
                        </div>
                        <div className="flex items-center gap-1 ml-4">
                          {vm.status === 'running' ? (
                            <>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation()
                                  handleVNC(vm.id)
                                }}
                                disabled={vncMutation.isPending}
                                className="p-2 text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition-colors"
                                title="VNC Console"
                              >
                                <Monitor className="h-4 w-4" />
                              </button>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation()
                                  handleStop(vm.id)
                                }}
                                disabled={stopMutation.isPending}
                                className="p-2 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                                title="Stop VM"
                              >
                                <Square className="h-4 w-4" />
                              </button>
                            </>
                          ) : (
                            <button
                              onClick={(e) => {
                                e.stopPropagation()
                                handleStart(vm.id)
                              }}
                              disabled={startMutation.isPending}
                              className="p-2 text-green-600 hover:bg-green-50 dark:hover:bg-green-900/20 rounded-lg transition-colors"
                              title="Start VM"
                            >
                              <Play className="h-4 w-4" />
                            </button>
                          )}
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              handleDelete(vm.id)
                            }}
                            disabled={deleteMutation.isPending}
                            className="p-2 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                            title="Delete VM"
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
                  <Server className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                  <p>No virtual machines found</p>
                  <p className="text-sm mt-2">Create a new VM to get started</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* VM Details */}
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle>VM Details</CardTitle>
              <CardDescription>
                {selectedVM ? 'Details for selected VM' : 'Select a VM to view details'}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {selectedVM && vmDetails ? (
                <div className="space-y-4">
                  <div>
                    <h3 className="font-semibold text-gray-900 dark:text-white mb-2">General</h3>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-500 dark:text-gray-400">Name:</span>
                        <span className="text-gray-900 dark:text-white font-medium">{vmDetails.name}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500 dark:text-gray-400">Status:</span>
                        <span className={`px-2 py-0.5 rounded text-xs ${getStatusColor(vmDetails.status)}`}>
                          {vmDetails.status}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500 dark:text-gray-400">VM ID:</span>
                        <span className="text-gray-900 dark:text-white font-mono text-xs">{vmDetails.vm_id}</span>
                      </div>
                    </div>
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900 dark:text-white mb-2">Resources</h3>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-500 dark:text-gray-400">vCPUs:</span>
                        <span className="text-gray-900 dark:text-white">{vmDetails.vcpus}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500 dark:text-gray-400">RAM:</span>
                        <span className="text-gray-900 dark:text-white">{formatMemory(vmDetails.ram_mb)}</span>
                      </div>
                    </div>
                  </div>
                  {vmDetails.mac_address && (
                    <div>
                      <h3 className="font-semibold text-gray-900 dark:text-white mb-2">Network</h3>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-gray-500 dark:text-gray-400">MAC:</span>
                          <span className="text-gray-900 dark:text-white font-mono text-xs">{vmDetails.mac_address}</span>
                        </div>
                        {vmDetails.ip_address && (
                          <div className="flex justify-between">
                            <span className="text-gray-500 dark:text-gray-400">IP:</span>
                            <span className="text-gray-900 dark:text-white">{vmDetails.ip_address}</span>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                  {vmDetails.vnc_port && (
                    <div>
                      <h3 className="font-semibold text-gray-900 dark:text-white mb-2">VNC</h3>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-gray-500 dark:text-gray-400">Port:</span>
                          <span className="text-gray-900 dark:text-white">{vmDetails.vnc_port}</span>
                        </div>
                        <button
                          onClick={() => handleVNC(selectedVM)}
                          className="w-full px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm"
                        >
                          Open VNC Console
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                  <p>Select a VM to view details</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Create VM Modal - Placeholder */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-2xl w-full mx-4">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Create Virtual Machine</h2>
            <p className="text-gray-500 dark:text-gray-400 mb-4">
              VM creation form will be implemented here. This requires image selection, resource configuration, and network settings.
            </p>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setShowCreateModal(false)}
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




