import { useState, useEffect, Suspense, lazy } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Activity,
  Server,
  Database,
  Users,
  HardDrive,
  Cpu,
  MemoryStick,
  Wifi,
  Clock,
  CheckCircle,
  AlertTriangle,
  XCircle,
  RefreshCw,
  TrendingUp,
  TrendingDown
} from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui'
import { LoadingSpinner } from '../components/LoadingSpinner'
import { apiHelpers } from '../lib/api'

// Lazy load chart components
const UsageChart = lazy(() => import('../components/charts').then(module => ({ default: module.UsageChart })))
const NetworkChart = lazy(() => import('../components/charts').then(module => ({ default: module.NetworkChart })))

interface SystemStats {
  cpu_percent: number
  memory_percent: number
  disk_percent: number
  network_io: {
    bytes_sent: number
    bytes_recv: number
    packets_sent: number
    packets_recv: number
  }
  load_average: number[]
  uptime_seconds: number
}

interface DatabaseStats {
  total_images: number
  total_machines: number
  total_targets: number
  active_sessions: number
  total_users: number
  database_size_mb: number
}

interface SessionStats {
  total_sessions: number
  active_sessions: number
  average_boot_time: number
  success_rate: number
  sessions_by_status: Record<string, number>
}

interface PerformanceMetrics {
  system: SystemStats
  database: DatabaseStats
  sessions: SessionStats
  timestamp: string
}

interface HealthCheck {
  status: 'healthy' | 'warning' | 'unhealthy'
  message: string
}

interface DetailedHealth {
  status: string
  timestamp: string
  checks: Record<string, HealthCheck>
}

interface ActiveSession {
  session_id: string
  status: string
  started_at: string
  boot_time?: string
  machine: {
    name: string
    mac_address: string
    ip_address?: string
  }
  target: {
    name: string
    iqn: string
  }
  client_ip?: string
  server_ip: string
  boot_method?: string
  target_iqn?: string
  target_portal?: string
}

function StatCard({ title, value, icon: Icon, color = 'blue', subtitle, trend }: {
  title: string
  value: string | number
  icon: any
  color?: 'blue' | 'green' | 'yellow' | 'red' | 'purple'
  subtitle?: string
  trend?: { value: number; isPositive: boolean }
}) {
  const colorClasses = {
    blue: {
      bg: 'bg-blue-50 dark:bg-blue-900/20',
      icon: 'bg-blue-500 text-white',
      text: 'text-blue-600 dark:text-blue-400',
      trend: 'text-blue-600 dark:text-blue-400'
    },
    green: {
      bg: 'bg-green-50 dark:bg-green-900/20',
      icon: 'bg-green-500 text-white',
      text: 'text-green-600 dark:text-green-400',
      trend: 'text-green-600 dark:text-green-400'
    },
    yellow: {
      bg: 'bg-yellow-50 dark:bg-yellow-900/20',
      icon: 'bg-yellow-500 text-white',
      text: 'text-yellow-600 dark:text-yellow-400',
      trend: 'text-yellow-600 dark:text-yellow-400'
    },
    red: {
      bg: 'bg-red-50 dark:bg-red-900/20',
      icon: 'bg-red-500 text-white',
      text: 'text-red-600 dark:text-red-400',
      trend: 'text-red-600 dark:text-red-400'
    },
    purple: {
      bg: 'bg-purple-50 dark:bg-purple-900/20',
      icon: 'bg-purple-500 text-white',
      text: 'text-purple-600 dark:text-purple-400',
      trend: 'text-purple-600 dark:text-purple-400'
    }
  }

  return (
    <Card className="hover:shadow-lg transition-all duration-200">
      <CardContent className="p-6">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <div className={`p-3 rounded-lg ${colorClasses[color].bg}`}>
              <Icon className={`h-6 w-6 ${colorClasses[color].icon}`} />
            </div>
          </div>
          <div className="ml-5 w-0 flex-1">
            <dl>
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">{title}</dt>
              <dd className="flex items-baseline">
                <div className="text-2xl font-semibold text-gray-900 dark:text-gray-100">{value}</div>
                {trend && (
                  <div className={`ml-2 flex items-baseline text-sm font-semibold ${colorClasses[color].trend}`}>
                    {trend.isPositive ? (
                      <TrendingUp className="self-center flex-shrink-0 h-4 w-4" />
                    ) : (
                      <TrendingDown className="self-center flex-shrink-0 h-4 w-4" />
                    )}
                    <span className="sr-only">{trend.isPositive ? 'Increased' : 'Decreased'} by</span>
                    {Math.abs(trend.value)}%
                  </div>
                )}
              </dd>
              {subtitle && (
                <dd className="text-sm text-gray-500 dark:text-gray-400 mt-1">{subtitle}</dd>
              )}
            </dl>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

function HealthStatus({ status }: { status: string }) {
  const statusConfig = {
    healthy: { icon: CheckCircle, color: 'text-green-500', bg: 'bg-green-50 dark:bg-green-900/20' },
    warning: { icon: AlertTriangle, color: 'text-yellow-500', bg: 'bg-yellow-50 dark:bg-yellow-900/20' },
    unhealthy: { icon: XCircle, color: 'text-red-500', bg: 'bg-red-50 dark:bg-red-900/20' }
  }

  const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.healthy
  const Icon = config.icon

  return (
    <div className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.bg} ${config.color}`}>
      <Icon className="w-3 h-3 mr-1" />
      {status}
    </div>
  )
}

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

function formatUptime(seconds: number): string {
  const days = Math.floor(seconds / 86400)
  const hours = Math.floor((seconds % 86400) / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  
  if (days > 0) return `${days}d ${hours}h ${minutes}m`
  if (hours > 0) return `${hours}h ${minutes}m`
  return `${minutes}m`
}

export default function MonitoringPage() {
  const [refreshInterval, setRefreshInterval] = useState(60000) // 60 seconds - reduced frequency
  const [chartData, setChartData] = useState<{
    cpu: Array<{ time: string; value: number }>
    memory: Array<{ time: string; value: number }>
    network: Array<{ time: string; sent: number; received: number }>
  }>({
    cpu: [],
    memory: [],
    network: []
  })

  // Fetch performance metrics with optimized caching
  const { data: metrics, isLoading: metricsLoading, error: metricsError, refetch: refetchMetrics } = useQuery({
    queryKey: ['monitoring-metrics'],
    queryFn: () => apiHelpers.getPerformanceMetrics(),
    refetchInterval: refreshInterval,
    retry: 2,
    retryDelay: 500,
    staleTime: 30000, // Consider data fresh for 30 seconds
    cacheTime: 300000, // Keep in cache for 5 minutes
    refetchOnWindowFocus: false, // Don't refetch on window focus
  })
  
  const { data: health, isLoading: healthLoading, error: healthError, refetch: refetchHealth } = useQuery({
    queryKey: ['monitoring-health'],
    queryFn: () => apiHelpers.getDetailedHealth(),
    refetchInterval: refreshInterval,
    retry: 2,
    retryDelay: 500,
    staleTime: 30000,
    cacheTime: 300000,
    refetchOnWindowFocus: false,
  })

  // Fetch active sessions with optimized caching
  const { data: activeSessions, isLoading: sessionsLoading, error: sessionsError, refetch: refetchSessions } = useQuery({
    queryKey: ['monitoring-sessions'],
    queryFn: () => apiHelpers.getActiveSessions(),
    refetchInterval: refreshInterval,
    retry: 2,
    retryDelay: 500,
    staleTime: 30000,
    cacheTime: 300000,
    refetchOnWindowFocus: false,
  })

  const handleRefresh = () => {
    refetchMetrics()
    refetchHealth()
    refetchSessions()
  }

  // Update chart data when metrics change
  useEffect(() => {
    if (metrics) {
      const now = new Date().toLocaleTimeString()
      const newData = {
        time: now,
        value: metrics.system.cpu_percent,
        sent: metrics.system.network_io.bytes_sent,
        received: metrics.system.network_io.bytes_recv
      }

      setChartData(prev => ({
        cpu: [...prev.cpu.slice(-19), { time: now, value: metrics.system.cpu_percent }],
        memory: [...prev.memory.slice(-19), { time: now, value: metrics.system.memory_percent }],
        network: [...prev.network.slice(-19), { time: now, sent: metrics.system.network_io.bytes_sent, received: metrics.system.network_io.bytes_recv }]
      }))
    }
  }, [metrics])

  // Show initial loading only if no data is available at all
  const hasAnyData = metrics || health || activeSessions
  const isInitialLoading = !hasAnyData && (metricsLoading || healthLoading || sessionsLoading)

  // Show initial loading spinner only when no data is available
  if (isInitialLoading) {
    return <LoadingSpinner size="lg" text="Loading monitoring data..." />
  }

  // Handle errors
  if (metricsError || healthError || sessionsError) {
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">System Monitoring</h1>
            <p className="mt-2 text-gray-600 dark:text-gray-400">
              Real-time performance metrics and system health
            </p>
          </div>
          <button
            onClick={handleRefresh}
            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </button>
        </div>
        
        <div className="text-center py-12">
          <AlertTriangle className="mx-auto h-12 w-12 text-red-500" />
          <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-gray-100">Failed to load monitoring data</h3>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            {metricsError && 'Performance metrics failed to load. '}
            {healthError && 'Health data failed to load. '}
            {sessionsError && 'Session data failed to load. '}
            Please check your connection and try again.
          </p>
          <div className="mt-6">
            <button
              onClick={handleRefresh}
              className="btn btn-primary btn-md"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Retry
            </button>
          </div>
        </div>
      </div>
    )
  }

  // Provide default values if data is missing
  const performanceMetrics = metrics as PerformanceMetrics || {
    system: {
      cpu_percent: 0,
      memory_percent: 0,
      disk_percent: 0,
      network_io: { bytes_sent: 0, bytes_recv: 0, packets_sent: 0, packets_recv: 0 },
      load_average: [0, 0, 0],
      uptime_seconds: 0
    },
    database: {
      total_images: 0,
      total_machines: 0,
      total_targets: 0,
      active_sessions: 0,
      total_users: 0,
      database_size_mb: 0
    },
    sessions: {
      total_sessions: 0,
      active_sessions: 0,
      average_boot_time: 0,
      success_rate: 0,
      sessions_by_status: {}
    },
    timestamp: new Date().toISOString()
  }
  
  const detailedHealth = health as DetailedHealth || {
    status: 'unknown',
    timestamp: new Date().toISOString(),
    checks: {}
  }
  
  const sessions = (activeSessions as ActiveSession[]) || []

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">System Monitoring</h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Real-time performance metrics and system health
          </p>
        </div>
        <button
          onClick={handleRefresh}
          className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </button>
      </div>

      {/* System Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {metricsLoading ? (
          <>
            <div className="animate-pulse bg-gray-200 dark:bg-gray-700 rounded-lg h-24"></div>
            <div className="animate-pulse bg-gray-200 dark:bg-gray-700 rounded-lg h-24"></div>
            <div className="animate-pulse bg-gray-200 dark:bg-gray-700 rounded-lg h-24"></div>
            <div className="animate-pulse bg-gray-200 dark:bg-gray-700 rounded-lg h-24"></div>
          </>
        ) : (
          <>
        <StatCard
          title="CPU Usage"
          value={`${performanceMetrics.system.cpu_percent.toFixed(1)}%`}
          icon={Cpu}
          color={performanceMetrics.system.cpu_percent > 80 ? 'red' : performanceMetrics.system.cpu_percent > 60 ? 'yellow' : 'green'}
        />
        <StatCard
          title="Memory Usage"
          value={`${performanceMetrics.system.memory_percent.toFixed(1)}%`}
          icon={MemoryStick}
          color={performanceMetrics.system.memory_percent > 80 ? 'red' : performanceMetrics.system.memory_percent > 60 ? 'yellow' : 'green'}
        />
        <StatCard
          title="Disk Usage"
          value={`${performanceMetrics.system.disk_percent.toFixed(1)}%`}
          icon={HardDrive}
          color={performanceMetrics.system.disk_percent > 90 ? 'red' : performanceMetrics.system.disk_percent > 80 ? 'yellow' : 'green'}
        />
        <StatCard
          title="Uptime"
          value={formatUptime(performanceMetrics.system.uptime_seconds)}
          icon={Clock}
          color="blue"
        />
          </>
        )}
      </div>

      {/* Database Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {metricsLoading ? (
          <>
            <div className="animate-pulse bg-gray-200 dark:bg-gray-700 rounded-lg h-24"></div>
            <div className="animate-pulse bg-gray-200 dark:bg-gray-700 rounded-lg h-24"></div>
            <div className="animate-pulse bg-gray-200 dark:bg-gray-700 rounded-lg h-24"></div>
            <div className="animate-pulse bg-gray-200 dark:bg-gray-700 rounded-lg h-24"></div>
            <div className="animate-pulse bg-gray-200 dark:bg-gray-700 rounded-lg h-24"></div>
            <div className="animate-pulse bg-gray-200 dark:bg-gray-700 rounded-lg h-24"></div>
          </>
        ) : (
          <>
        <StatCard
          title="Total Images"
          value={performanceMetrics.database.total_images}
          icon={HardDrive}
          color="blue"
        />
        <StatCard
          title="Total Machines"
          value={performanceMetrics.database.total_machines}
          icon={Server}
          color="green"
        />
        <StatCard
          title="Active Sessions"
          value={performanceMetrics.database.active_sessions}
          icon={Activity}
          color="purple"
        />
        <StatCard
          title="Total Users"
          value={performanceMetrics.database.total_users}
          icon={Users}
          color="yellow"
        />
        <StatCard
          title="Database Size"
          value={`${performanceMetrics.database.database_size_mb.toFixed(2)} MB`}
          icon={Database}
          color="blue"
        />
        <StatCard
          title="Success Rate"
          value={`${performanceMetrics.sessions.success_rate.toFixed(1)}%`}
          icon={CheckCircle}
          color={performanceMetrics.sessions.success_rate > 90 ? 'green' : performanceMetrics.sessions.success_rate > 70 ? 'yellow' : 'red'}
        />
          </>
        )}
      </div>

      {/* Health Status */}
      <Card>
        <CardHeader>
          <CardTitle>System Health</CardTitle>
        </CardHeader>
        <CardContent>
          {healthLoading ? (
            <div className="space-y-4">
              <div className="animate-pulse bg-gray-200 dark:bg-gray-700 rounded-lg h-16"></div>
              <div className="animate-pulse bg-gray-200 dark:bg-gray-700 rounded-lg h-16"></div>
              <div className="animate-pulse bg-gray-200 dark:bg-gray-700 rounded-lg h-16"></div>
            </div>
          ) : (
          <div className="space-y-4">
            {Object.entries(detailedHealth.checks).map(([check, status]) => (
              <div key={check} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <div className="flex items-center">
                  <HealthStatus status={status.status} />
                  <span className="ml-3 text-sm font-medium text-gray-900 dark:text-gray-100 capitalize">
                    {check.replace('_', ' ')}
                  </span>
                </div>
                <span className="text-sm text-gray-500 dark:text-gray-400">{status.message}</span>
              </div>
            ))}
          </div>
          )}
        </CardContent>
      </Card>

      {/* Active Sessions */}
      <Card>
        <CardHeader>
          <CardTitle>Active Sessions ({sessions.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {sessionsLoading ? (
            <div className="space-y-4">
              <div className="animate-pulse bg-gray-200 dark:bg-gray-700 rounded-lg h-20"></div>
              <div className="animate-pulse bg-gray-200 dark:bg-gray-700 rounded-lg h-20"></div>
            </div>
          ) : sessions.length === 0 ? (
            <div className="text-center py-8 text-gray-500 dark:text-gray-400">
              No active sessions
            </div>
          ) : (
            <div className="space-y-4">
              {sessions.map((session) => (
                <div key={session.session_id} className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <Activity className="h-5 w-5 text-blue-500 mr-3" />
                      <div>
                        <div className="font-medium text-gray-900 dark:text-gray-100">
                          {session.machine.name}
                        </div>
                        <div className="text-sm text-gray-500 dark:text-gray-400">
                          {session.session_id} • {session.target.name}
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                        {session.status}
                      </div>
                      <div className="text-sm text-gray-500 dark:text-gray-400">
                        {session.client_ip} → {session.server_ip}
                      </div>
                    </div>
                  </div>
                  {session.target_iqn && (
                    <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                      iSCSI: {session.target_iqn}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Usage Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
        <Suspense fallback={<div className="h-[200px] bg-gray-100 dark:bg-gray-800 rounded-lg animate-pulse" />}>
          <UsageChart
            data={chartData.cpu}
            title="CPU Usage"
            color="#ef4444"
            unit="%"
            type="area"
          />
        </Suspense>
        <Suspense fallback={<div className="h-[200px] bg-gray-100 dark:bg-gray-800 rounded-lg animate-pulse" />}>
          <UsageChart
            data={chartData.memory}
            title="Memory Usage"
            color="#3b82f6"
            unit="%"
            type="area"
          />
        </Suspense>
        <Suspense fallback={<div className="h-[200px] bg-gray-100 dark:bg-gray-800 rounded-lg animate-pulse" />}>
          <NetworkChart
            data={chartData.network}
          />
        </Suspense>
      </div>

      {/* Network I/O Stats */}
      <Card>
        <CardHeader>
          <CardTitle>Network I/O Statistics</CardTitle>
        </CardHeader>
        <CardContent>
          {metricsLoading ? (
            <div className="grid grid-cols-2 gap-4">
              <div className="animate-pulse bg-gray-200 dark:bg-gray-700 rounded-lg h-16"></div>
              <div className="animate-pulse bg-gray-200 dark:bg-gray-700 rounded-lg h-16"></div>
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                  {formatBytes(performanceMetrics.system.network_io.bytes_sent)}
                </div>
                <div className="text-sm text-gray-500 dark:text-gray-400">Bytes Sent</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                  {formatBytes(performanceMetrics.system.network_io.bytes_recv)}
                </div>
                <div className="text-sm text-gray-500 dark:text-gray-400">Bytes Received</div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
