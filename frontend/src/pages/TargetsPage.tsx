import { useState } from 'react'
import { useQuery } from 'react-query'
import { Target, Plus, Search } from 'lucide-react'
import { apiHelpers } from '../lib/api'

export default function TargetsPage() {
  const [searchTerm, setSearchTerm] = useState('')

  const { data: targetsData, isLoading } = useQuery(
    ['targets', searchTerm],
    () => apiHelpers.getTargets({
      search: searchTerm || undefined,
    })
  )

  const targets = targetsData?.data || []

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">iSCSI Targets</h1>
          <p className="mt-1 text-sm text-gray-500">
            Manage iSCSI targets for diskless boot
          </p>
        </div>
        <button className="btn btn-primary btn-md">
          <Plus className="h-4 w-4 mr-2" />
          Create Target
        </button>
      </div>

      {/* Search */}
      <div className="flex-1 max-w-md">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search targets..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="input pl-10"
          />
        </div>
      </div>

      {/* Content */}
      {isLoading ? (
        <div className="flex justify-center items-center h-64">
          <div className="spinner h-8 w-8" />
        </div>
      ) : targets.length === 0 ? (
        <div className="text-center py-12">
          <Target className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No targets</h3>
          <p className="mt-1 text-sm text-gray-500">
            Create your first iSCSI target to enable diskless boot.
          </p>
          <div className="mt-6">
            <button className="btn btn-primary btn-md">
              <Plus className="h-4 w-4 mr-2" />
              Create Target
            </button>
          </div>
        </div>
      ) : (
        <div className="card">
          <div className="card-content p-0">
            <div className="overflow-x-auto">
              <table className="table">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Machine</th>
                    <th>IQN</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {targets.map((target: any) => (
                    <tr key={target.id}>
                      <td>
                        <div>
                          <div className="font-medium text-gray-900">{target.name}</div>
                          <div className="text-sm text-gray-500">{target.description}</div>
                        </div>
                      </td>
                      <td>
                        <div className="text-sm text-gray-900">{target.machine_name}</div>
                      </td>
                      <td>
                        <div className="text-sm font-mono text-gray-900">{target.iqn}</div>
                      </td>
                      <td>
                        <span className={`badge ${
                          target.status === 'active' ? 'badge-success' : 'badge-secondary'
                        }`}>
                          {target.status}
                        </span>
                      </td>
                      <td>
                        <div className="flex space-x-2">
                          <button className="btn btn-ghost btn-sm">Edit</button>
                          <button className="btn btn-ghost btn-sm text-red-600">Delete</button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

