import { useState } from 'react'
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
  Cpu,
  MemoryStick,
  Users,
  Zap,
  Wifi,
  WifiOff
} from 'lucide-react'
import { apiHelpers } from '../lib/api'
import { useAuthStore } from '../stores/authStore'
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '../components/ui'
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

function StatsCard({ title, value, icon: Icon, trend, color = 'blue', subtitle, isLoading }: StatsCardProps) {
  const colorClasses = {
    blue: 'bg-blue-500 text-blue-600 bg-blue-50',
    green: 'bg-green-500 text-green-600 bg-green-50',
    yellow: 'bg-yellow-500 text-yellow-600 bg-yellow-50',
    red: 'bg-red-500 text-red-600 bg-red-50',
    purple: 'bg-purple-500 text-purple-600 bg-purple-50',
    indigo: 'bg-indigo-500 text-indigo-600 bg-indigo-50',
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
    <Card className="hover:shadow-lg transition-shadow duration-200">
      <CardContent className="p-6">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <div className={`p-3 rounded-lg ${colorClasses[color].split(' ')[2]}`}>
              <Icon className={`h-6 w-6 ${colorClasses[color].split(' ')[1]}`} />
            </div>
          </div>
          <div className="ml-5 w-0 flex-1">
            <dl>
              <dt className="text-sm font-medium text-gray-500 truncate">{title}</dt>
              <dd className="flex items-baseline">
                <div className="text-2xl font-semibold text-gray-900">{value}</div>
                {trend && (
                  <div className={`ml-2 flex items-baseline text-sm font-semibold ${
                    trend.isPositive ? 'text-green-600' : 'text-red-600'
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
                <dd className="text-sm text-gray-500 mt-1">{subtitle}</dd>
              )}
            </dl>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

interface ActivityItem {
  id: string
  type: 'success' | 'warning' | 'error' | 'info'
  message: string
  timestamp: string
  user?: string
}

function ActivityFeed({ activities }: { activities: ActivityItem[] }) {
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

  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent Activity</CardTitle>
        <CardDescription>Latest system events and user actions</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {activities.map((activity) => (
            <div
              key={activity.id}
              className={`flex items-start p-3 bg-gray-50 rounded-lg border-l-4 ${getActivityColor(activity.type)}`}
            >
              <div className="flex-shrink-0 mr-3">
                {getActivityIcon(activity.type)}
      </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm text-gray-900">{activity.message}</p>
                <div className="flex items-center mt-1 text-xs text-gray-500">
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
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

interface SystemStatusProps {
  status: 'healthy' | 'warning' | 'error'
  details: {
    database: boolean
    redis: boolean
    storage: boolean
    network: boolean
  }
}

function SystemStatus({ status, details }: SystemStatusProps) {
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
}

export default function DashboardPage() {
  const { user } = useAuthStore()
  const [refreshInterval, setRefreshInterval] = useState(30000) // 30 seconds

  // Fetch dashboard data
  const { data: healthData, isLoading: healthLoading } = useQuery({
    queryKey: ['health', 'detailed'],
    queryFn: () => apiHelpers.getDetailedHealth(),
    refetchInterval: refreshInterval,
  })

  const { data: storageData, isLoading: storageLoading } = useQuery({
    queryKey: ['storage'],
    queryFn: () => apiHelpers.getStorageInfo(),
    refetchInterval: refreshInterval,
  })

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
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-1 text-sm text-gray-500">
          Welcome back, {user?.full_name || user?.username}! Here's what's happening with your GGnet system.
        </p>
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
            <button className="flex flex-col items-center p-4 text-center hover:bg-gray-50 rounded-lg transition-colors">
              <HardDrive className="h-8 w-8 text-blue-600 mb-2" />
              <span className="text-sm font-medium text-gray-900">Upload Image</span>
            </button>
            <button className="flex flex-col items-center p-4 text-center hover:bg-gray-50 rounded-lg transition-colors">
              <Monitor className="h-8 w-8 text-green-600 mb-2" />
              <span className="text-sm font-medium text-gray-900">Add Machine</span>
            </button>
            <button className="flex flex-col items-center p-4 text-center hover:bg-gray-50 rounded-lg transition-colors">
              <Target className="h-8 w-8 text-purple-600 mb-2" />
              <span className="text-sm font-medium text-gray-900">Create Target</span>
            </button>
            <button className="flex flex-col items-center p-4 text-center hover:bg-gray-50 rounded-lg transition-colors">
              <Zap className="h-8 w-8 text-yellow-600 mb-2" />
              <span className="text-sm font-medium text-gray-900">Start Session</span>
            </button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}