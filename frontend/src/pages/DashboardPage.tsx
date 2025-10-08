import { useState, memo } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Activity,
  HardDrive,
  Monitor,
  Target,
  AlertTriangle,
  CheckCircle,
  Clock,
  TrendingUp,
  TrendingDown,
  Server,
  Database,
  Users,
  Zap,
  Wifi,
  WifiOff,
  Filter,
  RefreshCw
} from 'lucide-react'
import { apiHelpers } from '../lib/api'
import { useAuthStore } from '../stores/authStore'
import { Card, CardHeader, CardTitle, CardContent, CardDescription, Button } from '../components/ui'
import { LoadingSpinner } from '../components/LoadingSpinner'

interface StatsCardProps {
  title: string
  value: string | number
  icon: React.ElementType
  trend?: {
    value: number
    isPositive: boolean
  }
  color?: 'blue' | 'green' | 'yellow' | 'red' | 'purple' | 'indigo'
  subtitle?: string
  isLoading?: boolean
}

const StatsCard = memo(function StatsCard({ title, value, icon: Icon, trend, color = 'blue', subtitle, isLoading }: StatsCardProps) {
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
    },
    indigo: {
      bg: 'bg-indigo-50 dark:bg-indigo-900/20',
      icon: 'bg-indigo-500 text-white',
      text: 'text-indigo-600 dark:text-indigo-400',
      trend: 'text-indigo-600 dark:text-indigo-400'
    },
  }

  if (isLoading) {
    return (
      <Card>
        <CardContent className="p-6">
          <LoadingSpinner size="sm" />
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="hover:shadow-lg transition-all duration-200 dark:bg-gray-800 dark:border-gray-700">
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
                  <div className={`ml-2 flex items-baseline text-sm font-semibold ${
                    trend.isPositive ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                  }`}>
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
})

interface ActivityItem {
  id: string
  type: 'success' | 'warning' | 'error' | 'info'
  message: string
  timestamp: string
  user?: string
}

const ActivityFeed = memo(function ActivityFeed({ activities }: { activities: ActivityItem[] }) {
  const [filter, setFilter] = useState<'all' | 'success' | 'warning' | 'error' | 'info'>('all')
  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'success':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'warning':
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />
      case 'error':
        return <AlertTriangle className="h-4 w-4 text-red-500" />
      default:
        return <Activity className="h-4 w-4 text-blue-500" />
    }
  }

  const getActivityColor = (type: string) => {
    switch (type) {
      case 'success':
        return 'border-l-green-500'
      case 'warning':
        return 'border-l-yellow-500'
      case 'error':
        return 'border-l-red-500'
      default:
        return 'border-l-blue-500'
    }
  }

  const filteredActivities = filter === 'all' 
    ? activities 
    : activities.filter(activity => activity.type === filter)

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Recent Activity</CardTitle>
            <CardDescription>Latest system events and user actions</CardDescription>
          </div>
          <div className="flex items-center space-x-2">
            <Filter className="h-4 w-4 text-gray-400" />
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value as 'all' | 'success' | 'warning' | 'error' | 'info')}
              className="text-sm border border-gray-300 dark:border-gray-600 rounded-lg px-2 py-1 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
            >
              <option value="all">All</option>
              <option value="success">Success</option>
              <option value="warning">Warning</option>
              <option value="error">Error</option>
              <option value="info">Info</option>
            </select>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {filteredActivities.length === 0 ? (
            <div className="text-center py-8 text-gray-500 dark:text-gray-400">
              No activities found for the selected filter
            </div>
          ) : (
            filteredActivities.map((activity) => (
            <div
              key={activity.id}
                className={`flex items-start p-3 bg-gray-50 dark:bg-gray-800 rounded-lg border-l-4 ${getActivityColor(activity.type)}`}
            >
              <div className="flex-shrink-0 mr-3">
                {getActivityIcon(activity.type)}
      </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm text-gray-900 dark:text-gray-100">{activity.message}</p>
                <div className="flex items-center mt-1 text-xs text-gray-500 dark:text-gray-400">
                  <Clock className="h-3 w-3 mr-1" />
                  {new Date(activity.timestamp).toLocaleString()}
                  {activity.user && (
                    <>
                      <span className="mx-2">•</span>
                      <Users className="h-3 w-3 mr-1" />
                      {activity.user}
                    </>
                  )}
                    </div>
                  </div>
                </div>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  )
})

interface SystemStatusProps {
  status: 'healthy' | 'warning' | 'error'
  details: {
    database: boolean
    redis: boolean
    storage: boolean
    network: boolean
  }
}

const SystemStatus = memo(function SystemStatus({ status, details }: SystemStatusProps) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'text-green-600 bg-green-100'
      case 'warning':
        return 'text-yellow-600 bg-yellow-100'
      case 'error':
        return 'text-red-600 bg-red-100'
      default:
        return 'text-gray-600 bg-gray-100'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="h-5 w-5" />
      case 'warning':
        return <AlertTriangle className="h-5 w-5" />
      case 'error':
        return <AlertTriangle className="h-5 w-5" />
      default:
        return <Activity className="h-5 w-5" />
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>System Status</CardTitle>
        <CardDescription>Current system health and services</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(status)}`}>
            {getStatusIcon(status)}
            <span className="ml-2 capitalize">{status}</span>
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div className="flex items-center">
              <Database className="h-4 w-4 text-gray-400 mr-2" />
              <span className="text-sm text-gray-600">Database</span>
              <span className={`ml-auto h-2 w-2 rounded-full ${details.database ? 'bg-green-500' : 'bg-red-500'}`} />
            </div>
            <div className="flex items-center">
              <Server className="h-4 w-4 text-gray-400 mr-2" />
              <span className="text-sm text-gray-600">Redis</span>
              <span className={`ml-auto h-2 w-2 rounded-full ${details.redis ? 'bg-green-500' : 'bg-red-500'}`} />
            </div>
            <div className="flex items-center">
              <HardDrive className="h-4 w-4 text-gray-400 mr-2" />
              <span className="text-sm text-gray-600">Storage</span>
              <span className={`ml-auto h-2 w-2 rounded-full ${details.storage ? 'bg-green-500' : 'bg-red-500'}`} />
            </div>
            <div className="flex items-center">
              {details.network ? (
                <Wifi className="h-4 w-4 text-gray-400 mr-2" />
              ) : (
                <WifiOff className="h-4 w-4 text-gray-400 mr-2" />
              )}
              <span className="text-sm text-gray-600">Network</span>
              <span className={`ml-auto h-2 w-2 rounded-full ${details.network ? 'bg-green-500' : 'bg-red-500'}`} />
        </div>
      </div>
    </div>
      </CardContent>
    </Card>
  )
})

export default function DashboardPage() {
  const { user } = useAuthStore()
  const [refreshInterval] = useState(30000) // 30 seconds
  // Notifications are handled by NotificationProvider

  // Fetch dashboard data
  const { data: healthData } = useQuery({
    queryKey: ['health', 'detailed'],
    queryFn: () => apiHelpers.getDetailedHealth(),
    refetchInterval: refreshInterval,
  })

  // Storage data query - unused for now
  // const { data: storageData } = useQuery({
  //   queryKey: ['storage'],
  //   queryFn: () => apiHelpers.getStorageInfo(),
  //   refetchInterval: refreshInterval,
  // })

  // Mock data for demonstration
  const mockStats = {
    totalImages: 12,
    activeMachines: 8,
    runningSessions: 3,
    totalStorage: '2.4 TB',
    usedStorage: '1.8 TB',
    availableStorage: '600 GB'
  }

  const mockActivities: ActivityItem[] = [
    {
      id: '1',
      type: 'success',
      message: 'Image "Windows 11 Pro" uploaded successfully',
      timestamp: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
      user: 'admin'
    },
    {
      id: '2',
      type: 'info',
      message: 'Machine "PC-001" started diskless session',
      timestamp: new Date(Date.now() - 1000 * 60 * 15).toISOString(),
    },
    {
      id: '3',
      type: 'warning',
      message: 'Storage usage is above 80%',
      timestamp: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
    },
    {
      id: '4',
      type: 'success',
      message: 'Target "target-001" created successfully',
      timestamp: new Date(Date.now() - 1000 * 60 * 45).toISOString(),
      user: 'operator'
    },
    {
      id: '5',
      type: 'error',
      message: 'Failed to connect to machine "PC-003"',
      timestamp: new Date(Date.now() - 1000 * 60 * 60).toISOString(),
    }
  ]

  const systemStatus: SystemStatusProps = {
    status: healthData?.data?.status === 'healthy' ? 'healthy' : 'warning',
    details: {
      database: true,
      redis: true,
      storage: true,
      network: true
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Dashboard</h1>
            <p className="mt-2 text-gray-600 dark:text-gray-400">
              Welcome back, {user?.full_name || user?.username}! Here's what's happening with your GGnet system.
            </p>
          </div>
          <div className="flex items-center space-x-3">
            <Button variant="outline">
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        <StatsCard
          title="Total Images"
          value={mockStats.totalImages}
          icon={HardDrive}
          color="blue"
          subtitle="VHD/VHDX files"
          trend={{ value: 12, isPositive: true }}
        />
        <StatsCard
          title="Active Machines"
          value={mockStats.activeMachines}
          icon={Monitor}
          color="green"
          subtitle="Connected clients"
          trend={{ value: 5, isPositive: true }}
        />
        <StatsCard
          title="Running Sessions"
          value={mockStats.runningSessions}
          icon={Activity}
          color="purple"
          subtitle="Diskless boots"
          trend={{ value: 2, isPositive: false }}
        />
        <StatsCard
          title="Storage Used"
          value={`${mockStats.usedStorage} / ${mockStats.totalStorage}`}
          icon={Database}
          color="indigo"
          subtitle={`${mockStats.availableStorage} available`}
          trend={{ value: 8, isPositive: false }}
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* System Status */}
        <div className="lg:col-span-1">
          <SystemStatus {...systemStatus} />
        </div>

        {/* Activity Feed */}
        <div className="lg:col-span-2">
          <ActivityFeed activities={mockActivities} />
        </div>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
          <CardDescription>Common tasks and shortcuts</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <button className="flex flex-col items-center p-4 text-center hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg transition-colors">
              <HardDrive className="h-8 w-8 text-blue-600 mb-2" />
              <span className="text-sm font-medium text-gray-900 dark:text-gray-100">Upload Image</span>
            </button>
            <button className="flex flex-col items-center p-4 text-center hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg transition-colors">
              <Monitor className="h-8 w-8 text-green-600 mb-2" />
              <span className="text-sm font-medium text-gray-900 dark:text-gray-100">Add Machine</span>
            </button>
            <button className="flex flex-col items-center p-4 text-center hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg transition-colors">
              <Target className="h-8 w-8 text-purple-600 mb-2" />
              <span className="text-sm font-medium text-gray-900 dark:text-gray-100">Create Target</span>
            </button>
            <button className="flex flex-col items-center p-4 text-center hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg transition-colors">
              <Zap className="h-8 w-8 text-yellow-600 mb-2" />
              <span className="text-sm font-medium text-gray-900 dark:text-gray-100">Start Session</span>
            </button>
          </div>
        </CardContent>
      </Card>

      {/* Notification Center - removed as it's handled by NotificationProvider */}
    </div>
  )
}