import { useState } from 'react'
import { useQuery } from 'react-query'
import { Activity, Play, Square, Search } from 'lucide-react'
import { apiHelpers } from '../lib/api'

export default function SessionsPage() {
  const [searchTerm, setSearchTerm] = useState('')

  const { data: sessionsData, isLoading } = useQuery(
    ['sessions', searchTerm],
    () => apiHelpers.getSessions({
      search: searchTerm || undefined,
    }),
    {
      refetchInterval: 5000, // Refresh every 5 seconds
    }
  )

  const sessions = sessionsData?.data || []

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'badge-success'
      case 'starting':
        return 'badge-warning'
      case 'stopping':
        return 'badge-warning'
      case 'stopped':
        return 'badge-secondary'
      case 'error':
        return 'badge-error'
      default:
        return 'badge-secondary'
    }
  }

  const formatDuration = (seconds: number | null) => {
    if (!seconds) return '-'
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = seconds % 60
    
    if (hours > 0) {
      return `${hours}h ${minutes}m ${secs}s`
    } else if (minutes > 0) {
      return `${minutes}m ${secs}s`
    } else {
      return `${secs}s`
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Boot Sessions</h1>
          <p className="mt-1 text-sm text-gray-500">
            Monitor active and historical diskless boot sessions
          </p>
        </div>
        <button className="btn btn-primary btn-md">
          <Play className="h-4 w-4 mr-2" />
          Start Session
        </button>
      </div>

      {/* Search */}
      <div className="flex-1 max-w-md">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search sessions..."
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
      ) : sessions.length === 0 ? (
        <div className="text-center py-12">
          <Activity className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No sessions</h3>
          <p className="mt-1 text-sm text-gray-500">
            No boot sessions found. Start a session to begin diskless boot.
          </p>
          <div className="mt-6">
            <button className="btn btn-primary btn-md">
              <Play className="h-4 w-4 mr-2" />
              Start Session
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
                    <th>Session ID</th>
                    <th>Machine</th>
                    <th>Target</th>
                    <th>Status</th>
                    <th>Duration</th>
                    <th>Started</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {sessions.map((session: any) => (
                    <tr key={session.id}>
                      <td>
                        <div className="font-mono text-sm">{session.session_id}</div>
                      </td>
                      <td>
                        <div className="text-sm text-gray-900">{session.machine_name}</div>
                      </td>
                      <td>
                        <div className="text-sm text-gray-900">{session.target_name}</div>
                      </td>
                      <td>
                        <span className={`badge ${getStatusColor(session.status)}`}>
                          {session.status}
                        </span>
                      </td>
                      <td>
                        <div className="text-sm text-gray-900">
                          {formatDuration(session.duration_seconds)}
                        </div>
                      </td>
                      <td>
                        <div className="text-sm text-gray-900">
                          {new Date(session.started_at).toLocaleString()}
                        </div>
                      </td>
                      <td>
                        <div className="flex space-x-2">
                          {session.status === 'active' && (
                            <button className="btn btn-ghost btn-sm text-red-600">
                              <Square className="h-3 w-3 mr-1" />
                              Stop
                            </button>
                          )}
                          <button className="btn btn-ghost btn-sm">View</button>
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

