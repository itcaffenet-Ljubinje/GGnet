import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle, Button } from '../components/ui'
import { 
  Monitor, 
  Plus, 
  Edit, 
  Trash2, 
  Power, 
  PowerOff, 
  Search, 
  Filter,
  RefreshCw,
  Eye,
  Settings
} from 'lucide-react'
import { apiHelpers } from '../lib/api'
import { useNotifications } from '../components/notifications'
import { clsx } from 'clsx'
import MachineModal from '../components/MachineModal'

interface Machine {
  id: number
  name: string
  description?: string
  mac_address: string
  ip_address?: string
  hostname?: string
  boot_mode: string
  secure_boot_enabled: boolean
  status: string
  is_online: boolean
  location?: string
  room?: string
  asset_tag?: string
  created_at: string
  last_seen?: string
  last_boot?: string
  boot_count: number
}

interface MachineStats {
  total: number
  active: number
  online: number
  offline: number
}

export default function MachinesPage() {
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [selectedMachines, setSelectedMachines] = useState<number[]>([])
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [editingMachine, setEditingMachine] = useState<Machine | null>(null)
  
  const { addNotification } = useNotifications()
  const queryClient = useQueryClient()

  // Fetch machines
  const { data: machines = [], isLoading, error, refetch } = useQuery({
    queryKey: ['machines', searchTerm, statusFilter],
    queryFn: () => apiHelpers.getMachines({ 
      search: searchTerm || undefined,
      status: statusFilter || undefined 
    }),
    staleTime: 30000,
    refetchInterval: 60000,
  })

  // Calculate stats
  const stats: MachineStats = machines.reduce((acc: any, machine: any) => {
    acc.total++
    if (machine.status === 'active') acc.active++
    if (machine.is_online) acc.online++
    else acc.offline++
    return acc
  }, { total: 0, active: 0, online: 0, offline: 0 })

  // Delete machine mutation
  const deleteMachineMutation = useMutation({
    mutationFn: (id: number) => apiHelpers.deleteMachine(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['machines'] })
      addNotification({
        type: 'success',
        message: 'Machine deleted successfully'
      })
    },
    onError: (error: any) => {
      addNotification({
        type: 'error',
        message: `Failed to delete machine: ${error.message}`
      })
    }
  })

  // Toggle machine status mutation
  const toggleStatusMutation = useMutation({
    mutationFn: ({ id, status }: { id: number; status: string }) => 
      apiHelpers.updateMachine(id, { status }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['machines'] })
      addNotification({
        type: 'success',
        message: 'Machine status updated successfully'
      })
    },
    onError: (error: any) => {
      addNotification({
        type: 'error',
        message: `Failed to update machine status: ${error.message}`
      })
    }
  })

  const handleDelete = (id: number) => {
    if (window.confirm('Are you sure you want to delete this machine?')) {
      deleteMachineMutation.mutate(id)
    }
  }

  const handleToggleStatus = (machine: Machine) => {
    const newStatus = machine.status === 'active' ? 'inactive' : 'active'
    toggleStatusMutation.mutate({ id: machine.id, status: newStatus })
  }

  const handleSelectMachine = (id: number) => {
    setSelectedMachines(prev => 
      prev.includes(id) 
        ? prev.filter(mid => mid !== id)
        : [...prev, id]
    )
  }

  const handleSelectAll = () => {
    if (selectedMachines.length === machines.length) {
      setSelectedMachines([])
    } else {
      setSelectedMachines(machines.map((m: any) => m.id))
    }
  }

  const handleEdit = (machine: any) => {
    setEditingMachine(machine)
    setShowEditModal(true)
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
      case 'inactive':
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200'
      case 'maintenance':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
      case 'retired':
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200'
    }
  }

  const getOnlineStatus = (isOnline: boolean) => {
    return isOnline 
      ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
      : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
  }

  if (error) {
  return (
      <div className="space-y-6">
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <Monitor className="h-8 w-8 text-red-400" />
            </div>
            <div className="ml-3">
              <h3 className="text-lg font-medium text-red-800 dark:text-red-200">
                Error Loading Machines
              </h3>
              <p className="mt-1 text-sm text-red-700 dark:text-red-300">
                {error.message || 'Failed to load machines'}
              </p>
              <button
                onClick={() => refetch()}
                className="mt-2 text-sm text-red-600 hover:text-red-500 dark:text-red-400 dark:hover:text-red-300"
              >
                Try again
              </button>
          </div>
        </div>
      </div>
    </div>
  )
}

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
            Machine Management
          </h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Manage your diskless client machines
          </p>
        </div>
        <div className="flex space-x-3">
          <Button
            variant="outline"
            onClick={() => {
              queryClient.invalidateQueries({ queryKey: ['machines'] })
              refetch()
            }}
            disabled={isLoading}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button onClick={() => setShowCreateModal(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Add Machine
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Machines</CardTitle>
            <Monitor className="h-4 w-4 text-gray-500 dark:text-gray-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total}</div>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              All registered machines
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active</CardTitle>
            <Power className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{stats.active}</div>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Ready for use
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Online</CardTitle>
            <Monitor className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">{stats.online}</div>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Currently connected
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Offline</CardTitle>
            <PowerOff className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{stats.offline}</div>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Not connected
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="flex-1">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search machines..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-800 dark:text-gray-100"
            />
          </div>
        </div>
        <div className="sm:w-48">
          <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-800 dark:text-gray-100"
          >
            <option value="">All Status</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
            <option value="maintenance">Maintenance</option>
            <option value="retired">Retired</option>
          </select>
        </div>
      </div>
        </CardContent>
      </Card>

      {/* Machines Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Machines</CardTitle>
            {selectedMachines.length > 0 && (
              <div className="flex items-center space-x-2">
                <span className="text-sm text-gray-500">
                  {selectedMachines.length} selected
                </span>
                <Button variant="outline" size="sm">
                  Bulk Actions
                </Button>
              </div>
            )}
          </div>
        </CardHeader>
        <CardContent>
      {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <RefreshCw className="h-8 w-8 animate-spin text-gray-400" />
        </div>
      ) : machines.length === 0 ? (
        <div className="text-center py-12">
          <Monitor className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-gray-100">
                No machines found
              </h3>
              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                Get started by creating a new machine.
          </p>
          <div className="mt-6">
                <Button onClick={() => setShowCreateModal(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Add Machine
                </Button>
          </div>
        </div>
      ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                <thead className="bg-gray-50 dark:bg-gray-800">
                  <tr>
                    <th className="px-6 py-3 text-left">
                      <input
                        type="checkbox"
                        checked={selectedMachines.length === machines.length}
                        onChange={handleSelectAll}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Machine
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      MAC Address
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Online
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Location
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Last Seen
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                  {machines.map((machine: any) => (
                    <tr key={machine.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <input
                          type="checkbox"
                          checked={selectedMachines.includes(machine.id)}
                          onChange={() => handleSelectMachine(machine.id)}
                          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                            {machine.name}
                          </div>
                          {machine.description && (
                            <div className="text-sm text-gray-500 dark:text-gray-400">
                              {machine.description}
                            </div>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                        {machine.mac_address}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={clsx(
                          "px-2 inline-flex text-xs leading-5 font-semibold rounded-full",
                          getStatusColor(machine.status)
                        )}>
                          {machine.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={clsx(
                          "px-2 inline-flex text-xs leading-5 font-semibold rounded-full",
                          getOnlineStatus(machine.is_online)
                        )}>
                          {machine.is_online ? 'Online' : 'Offline'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                        {machine.location || '-'}
                        {machine.room && <span className="text-gray-500"> / {machine.room}</span>}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                        {machine.last_seen ? new Date(machine.last_seen).toLocaleDateString() : 'Never'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <div className="flex items-center space-x-2">
                          <button
                            onClick={() => handleEdit(machine)}
                            className="text-blue-600 hover:text-blue-900 dark:text-blue-400 dark:hover:text-blue-300"
                          >
                            <Edit className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => handleToggleStatus(machine)}
                            className={clsx(
                              "hover:opacity-75",
                              machine.status === 'active' 
                                ? "text-red-600 hover:text-red-900 dark:text-red-400 dark:hover:text-red-300"
                                : "text-green-600 hover:text-green-900 dark:text-green-400 dark:hover:text-green-300"
                            )}
                          >
                            {machine.status === 'active' ? (
                              <PowerOff className="h-4 w-4" />
                            ) : (
                              <Power className="h-4 w-4" />
                            )}
                          </button>
                          <button
                            onClick={() => handleDelete(machine.id)}
                            className="text-red-600 hover:text-red-900 dark:text-red-400 dark:hover:text-red-300"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
        </div>
      )}
        </CardContent>
      </Card>

      {/* Machine Modal */}
      <MachineModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        mode="create"
      />

      <MachineModal
        isOpen={showEditModal}
        onClose={() => setShowEditModal(false)}
        machine={editingMachine}
        mode="edit"
      />
    </div>
  )
}