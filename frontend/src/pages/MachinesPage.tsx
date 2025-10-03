import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Monitor, Plus, Search, Wifi, WifiOff } from 'lucide-react'
import { apiHelpers } from '../lib/api'

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
  created_at: string
}

function MachineCard({ machine }: { machine: Machine }) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'badge-success'
      case 'maintenance':
        return 'badge-warning'
      case 'retired':
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
              <Monitor className="h-8 w-8 text-gray-400" />
            </div>
            <div className="min-w-0 flex-1">
              <h3 className="text-sm font-medium text-gray-900 truncate">
                {machine.name}
              </h3>
              <p className="text-sm text-gray-500 truncate">
                {machine.description || 'No description'}
              </p>
              <div className="mt-2 space-y-1">
                <div className="flex items-center text-xs text-gray-500">
                  <span className="font-medium">MAC:</span>
                  <span className="ml-1 font-mono">{machine.mac_address}</span>
                </div>
                {machine.ip_address && (
                  <div className="flex items-center text-xs text-gray-500">
                    <span className="font-medium">IP:</span>
                    <span className="ml-1 font-mono">{machine.ip_address}</span>
                  </div>
                )}
                {machine.location && (
                  <div className="flex items-center text-xs text-gray-500">
                    <span className="font-medium">Location:</span>
                    <span className="ml-1">{machine.location}</span>
                    {machine.room && <span className="ml-1">({machine.room})</span>}
                  </div>
                )}
              </div>
              <div className="mt-2 flex items-center space-x-2">
                <span className={`badge ${getStatusColor(machine.status)}`}>
                  {machine.status}
                </span>
                <div className="flex items-center">
                  {machine.is_online ? (
                    <Wifi className="h-3 w-3 text-green-500" />
                  ) : (
                    <WifiOff className="h-3 w-3 text-gray-400" />
                  )}
                  <span className="ml-1 text-xs text-gray-500">
                    {machine.is_online ? 'Online' : 'Offline'}
                  </span>
                </div>
                {machine.secure_boot_enabled && (
                  <span className="badge badge-primary text-xs">SecureBoot</span>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default function MachinesPage() {
  const [searchTerm, setSearchTerm] = useState('')
  const [filterStatus, setFilterStatus] = useState('')

  const { data: machinesData, isLoading, error } = useQuery({
    queryKey: ['machines', searchTerm, filterStatus],
    queryFn: () => apiHelpers.getMachines({
      search: searchTerm || undefined,
      status: filterStatus || undefined,
    })
  })

  const machines = (machinesData as any)?.data || []

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Machines</h1>
          <p className="mt-1 text-sm text-gray-500">
            Manage client machines for diskless boot
          </p>
        </div>
        <button className="btn btn-primary btn-md">
          <Plus className="h-4 w-4 mr-2" />
          Add Machine
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="flex-1">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search machines..."
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
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
            <option value="maintenance">Maintenance</option>
            <option value="retired">Retired</option>
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
          <p className="text-gray-500">Failed to load machines</p>
        </div>
      ) : machines.length === 0 ? (
        <div className="text-center py-12">
          <Monitor className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No machines</h3>
          <p className="mt-1 text-sm text-gray-500">
            Get started by adding your first client machine.
          </p>
          <div className="mt-6">
            <button className="btn btn-primary btn-md">
              <Plus className="h-4 w-4 mr-2" />
              Add Machine
            </button>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {machines.map((machine: Machine) => (
            <MachineCard key={machine.id} machine={machine} />
          ))}
        </div>
      )}
    </div>
  )
}

