import React, { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle, Button } from '../components/ui'
import { 
  Activity, 
  Play, 
  Square, 
  RefreshCw, 
  Eye, 
  AlertTriangle,
  CheckCircle,
  Clock,
  Monitor,
  HardDrive,
  Wifi,
  WifiOff,
  Calendar
} from 'lucide-react'
import { apiHelpers } from '../lib/api'
import { useNotifications } from '../components/notifications'
import { clsx } from 'clsx'

interface SessionStats {
  total_sessions: number
  active_sessions: number
  completed_sessions: number
  failed_sessions: number
  total_uptime_hours: number
  average_session_duration: number
  sessions_today: number
  sessions_this_week: number
}

interface ActiveSession {
  id: number
  session_id: string
  machine_name: string
  machine_mac: string
  client_ip: string
  target_name: string
  image_name: string
  started_at: string
  duration_minutes: number
  status: string
  iscsi_connection: boolean
  boot_progress?: string
}

interface RealtimeData {
  active_sessions: any[]
  recent_sessions: any[]
  system_stats: any
  iscsi_status: any
  timestamp: string
}

export default function SessionsPage() {
  const [selectedSessions, setSelectedSessions] = useState<string[]>([])
  const [autoRefresh, setAutoRefresh] = useState(true)
  
  const { addNotification } = useNotifications()
  const queryClient = useQueryClient()

  // Fetch session stats
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['session-stats'],
    queryFn: () => apiHelpers.getSessionStats(),
    refetchInterval: autoRefresh ? 30000 : false,
  })

  // Fetch active sessions
  const { data: activeSessions = [], isLoading: activeLoading, refetch: refetchActive } = useQuery({
    queryKey: ['active-sessions'],
    queryFn: () => apiHelpers.getActiveSessionsDetailed(),
    refetchInterval: autoRefresh ? 10000 : false,
  })

  // Fetch realtime data
  const { data: realtimeData, isLoading: realtimeLoading } = useQuery({
    queryKey: ['realtime-sessions'],
    queryFn: () => apiHelpers.getRealtimeSessionData(),
    refetchInterval: autoRefresh ? 5000 : false,
  })

  // Kill session mutation
  const killSessionMutation = useMutation({
    mutationFn: (sessionId: string) => apiHelpers.killSession(sessionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['active-sessions'] })
      queryClient.invalidateQueries({ queryKey: ['session-stats'] })
      addNotification({
        type: 'success',
        title: 'Success',
        message: 'Session terminated successfully'
      })
    },
    onError: (error: any) => {
      addNotification({
        type: 'error',
        title: 'Error',
        message: `Failed to terminate session: ${error.message}`
      })
    }
  })

  const handleKillSession = (sessionId: string) => {
    if (window.confirm('Are you sure you want to terminate this session?')) {
      killSessionMutation.mutate(sessionId)
    }
  }

  const handleSelectSession = (sessionId: string) => {
    setSelectedSessions(prev => 
      prev.includes(sessionId) 
        ? prev.filter(id => id !== sessionId)
        : [...prev, sessionId]
    )
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
      case 'completed':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
      case 'failed':
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
      case 'starting':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <CheckCircle className="h-4 w-4" />
      case 'completed':
        return <CheckCircle className="h-4 w-4" />
      case 'failed':
        return <AlertTriangle className="h-4 w-4" />
      case 'starting':
        return <Clock className="h-4 w-4 animate-pulse" />
      default:
        return <Activity className="h-4 w-4" />
    }
  }

  const formatDuration = (minutes: number) => {
    if (minutes < 60) {
      return `${minutes}m`
    }
    const hours = Math.floor(minutes / 60)
    const remainingMinutes = minutes % 60
    return `${hours}h ${remainingMinutes}m`
  }

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
            Session Management
          </h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Monitor and manage active diskless sessions
          </p>
        </div>
        <div className="flex space-x-3">
          <Button
            variant="outline"
            onClick={() => {
              refetchActive()
              queryClient.invalidateQueries({ queryKey: ['session-stats'] })
              queryClient.invalidateQueries({ queryKey: ['realtime-sessions'] })
            }}
            disabled={activeLoading || statsLoading || realtimeLoading}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${activeLoading || statsLoading || realtimeLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button
            variant={autoRefresh ? "primary" : "outline"}
            onClick={() => setAutoRefresh(!autoRefresh)}
          >
            {autoRefresh ? 'Auto Refresh ON' : 'Auto Refresh OFF'}
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 lg:grid-cols-8 gap-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total</CardTitle>
              <Activity className="h-4 w-4 text-gray-500 dark:text-gray-400" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total_sessions}</div>
              <p className="text-xs text-gray-500 dark:text-gray-400">All time</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active</CardTitle>
              <Play className="h-4 w-4 text-green-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">{stats.active_sessions}</div>
              <p className="text-xs text-gray-500 dark:text-gray-400">Running now</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Completed</CardTitle>
              <CheckCircle className="h-4 w-4 text-blue-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-blue-600">{stats.completed_sessions}</div>
              <p className="text-xs text-gray-500 dark:text-gray-400">Successful</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Failed</CardTitle>
              <AlertTriangle className="h-4 w-4 text-red-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-red-600">{stats.failed_sessions}</div>
              <p className="text-xs text-gray-500 dark:text-gray-400">Errors</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Uptime</CardTitle>
              <Clock className="h-4 w-4 text-purple-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-purple-600">{stats.total_uptime_hours}h</div>
              <p className="text-xs text-gray-500 dark:text-gray-400">Total time</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Avg Duration</CardTitle>
              <Clock className="h-4 w-4 text-indigo-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-indigo-600">{stats.average_session_duration}m</div>
              <p className="text-xs text-gray-500 dark:text-gray-400">Per session</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Today</CardTitle>
              <Calendar className="h-4 w-4 text-orange-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-orange-600">{stats.sessions_today}</div>
              <p className="text-xs text-gray-500 dark:text-gray-400">Sessions</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">This Week</CardTitle>
              <Calendar className="h-4 w-4 text-teal-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-teal-600">{stats.sessions_this_week}</div>
              <p className="text-xs text-gray-500 dark:text-gray-400">Sessions</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* System Stats */}
      {realtimeData?.system_stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">CPU Usage</CardTitle>
              <Monitor className="h-4 w-4 text-blue-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{realtimeData.system_stats.cpu?.percent?.toFixed(1) || 0}%</div>
              <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                <div
                  className="bg-blue-600 h-2 rounded-full"
                  style={{ width: `${realtimeData.system_stats.cpu?.percent || 0}%` }}
                />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Memory Usage</CardTitle>
              <HardDrive className="h-4 w-4 text-green-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{realtimeData.system_stats.memory?.percent?.toFixed(1) || 0}%</div>
              <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                <div
                  className="bg-green-600 h-2 rounded-full"
                  style={{ width: `${realtimeData.system_stats.memory?.percent || 0}%` }}
                />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Disk Usage</CardTitle>
              <HardDrive className="h-4 w-4 text-yellow-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{realtimeData.system_stats.disk?.percent?.toFixed(1) || 0}%</div>
              <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                <div
                  className="bg-yellow-600 h-2 rounded-full"
                  style={{ width: `${realtimeData.system_stats.disk?.percent || 0}%` }}
                />
      </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">iSCSI Targets</CardTitle>
              <Wifi className="h-4 w-4 text-purple-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{realtimeData.iscsi_status?.total_targets || 0}</div>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {realtimeData.iscsi_status?.active_sessions || 0} active sessions
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Active Sessions */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Play className="h-5 w-5 mr-2 text-green-500" />
            Active Sessions ({activeSessions.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          {activeLoading ? (
            <div className="flex items-center justify-center py-12">
              <RefreshCw className="h-8 w-8 animate-spin text-gray-400" />
            </div>
          ) : activeSessions.length === 0 ? (
        <div className="text-center py-12">
          <Activity className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-gray-100">
                No active sessions
              </h3>
              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                Start a machine to see active sessions here.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {activeSessions.map((session: any) => (
                <div
                  key={session.id}
                  className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <input
                        type="checkbox"
                        checked={selectedSessions.includes(session.session_id)}
                        onChange={() => handleSelectSession(session.session_id)}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                      
                      <div className="flex items-center space-x-2">
                        {getStatusIcon(session.status)}
                        <span className={clsx(
                          "px-2 inline-flex text-xs leading-5 font-semibold rounded-full",
                          getStatusColor(session.status)
                        )}>
                          {session.status}
                        </span>
                      </div>

                      <div>
                        <div className="font-medium text-gray-900 dark:text-gray-100">
                          {session.machine_name}
                        </div>
                        <div className="text-sm text-gray-500 dark:text-gray-400">
                          {session.machine_mac} • {session.client_ip}
                        </div>
                      </div>

                      <div>
                        <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                          {session.target_name}
                        </div>
                        <div className="text-sm text-gray-500 dark:text-gray-400">
                          {session.image_name}
                        </div>
                      </div>

                      <div className="flex items-center space-x-2">
                        {session.iscsi_connection ? (
                          <Wifi className="h-4 w-4 text-green-500" />
                        ) : (
                          <WifiOff className="h-4 w-4 text-red-500" />
                        )}
                        <span className="text-sm text-gray-500 dark:text-gray-400">
                          {session.iscsi_connection ? 'Connected' : 'Disconnected'}
                        </span>
                      </div>

                      {session.boot_progress && (
                        <div>
                          <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                            Boot Progress
                          </div>
                          <div className="text-sm text-gray-500 dark:text-gray-400">
                            {session.boot_progress}
                          </div>
                        </div>
                      )}
                    </div>

                    <div className="flex items-center space-x-4">
                      <div className="text-right">
                        <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                          {formatDuration(session.duration_minutes)}
                        </div>
                        <div className="text-sm text-gray-500 dark:text-gray-400">
                          Running
                        </div>
                      </div>

                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => handleKillSession(session.session_id)}
                          className="text-red-600 hover:text-red-900 dark:text-red-400 dark:hover:text-red-300"
                          disabled={killSessionMutation.isPending}
                        >
                          <Square className="h-4 w-4" />
            </button>
          </div>
        </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Recent Sessions */}
      {realtimeData?.recent_sessions && realtimeData.recent_sessions.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Clock className="h-5 w-5 mr-2 text-gray-500" />
              Recent Sessions (Last 24 Hours)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                <thead className="bg-gray-50 dark:bg-gray-800">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Machine
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Target
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Duration
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Started
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Ended
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                  {realtimeData.recent_sessions.map((session: any) => (
                    <tr key={session.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                            {session.machine_name}
                          </div>
                          <div className="text-sm text-gray-500 dark:text-gray-400">
                            {session.machine_mac}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                            {session.target_name}
                          </div>
                          <div className="text-sm text-gray-500 dark:text-gray-400">
                            {session.image_name}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={clsx(
                          "px-2 inline-flex text-xs leading-5 font-semibold rounded-full",
                          getStatusColor(session.status)
                        )}>
                          {session.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                        {session.duration_seconds ? formatDuration(Math.floor(session.duration_seconds / 60)) : '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                          {new Date(session.started_at).toLocaleString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                        {session.ended_at ? new Date(session.ended_at).toLocaleString() : '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}