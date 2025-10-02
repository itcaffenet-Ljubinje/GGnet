import { useQuery } from 'react-query'
import {
  Activity,
  HardDrive,
  Monitor,
  Target,
  AlertTriangle,
  CheckCircle,
  Clock,
  TrendingUp,
} from 'lucide-react'
import { apiHelpers } from '../lib/api'
import { useAuthStore } from '../stores/authStore'

interface StatsCardProps {
  title: string
  value: string | number
  icon: React.ElementType
  trend?: {
    value: number
    isPositive: boolean
  }
  color?: 'blue' | 'green' | 'yellow' | 'red' | 'purple'
}

function StatsCard({ title, value, icon: Icon, trend, color = 'blue' }: StatsCardProps) {
  const colorClasses = {
    blue: 'bg-blue-500 text-blue-600 bg-blue-50',
    green: 'bg-green-500 text-green-600 bg-green-50',
    yellow: 'bg-yellow-500 text-yellow-600 bg-yellow-50',
    red: 'bg-red-500 text-red-600 bg-red-50',
    purple: 'bg-purple-500 text-purple-600 bg-purple-50',
  }

  return (
    <div className="card">
      <div className="card-content">
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
                    <TrendingUp className={`self-center flex-shrink-0 h-4 w-4 ${
                      trend.isPositive ? 'text-green-500' : 'text-red-500 transform rotate-180'
                    }`} />
                    <span className="ml-1">{Math.abs(trend.value)}%</span>
                  </div>
                )}
              </dd>
            </dl>
          </div>
        </div>
      </div>
    </div>
  )
}

interface ActivityItem {
  id: string
  type: 'session_started' | 'session_stopped' | 'image_uploaded' | 'machine_created'
  message: string
  timestamp: string
  user?: string
}

function ActivityFeed({ activities }: { activities: ActivityItem[] }) {
  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'session_started':
        return <CheckCircle className="h-5 w-5 text-green-500" />
      case 'session_stopped':
        return <Clock className="h-5 w-5 text-gray-500" />
      case 'image_uploaded':
        return <HardDrive className="h-5 w-5 text-blue-500" />
      case 'machine_created':
        return <Monitor className="h-5 w-5 text-purple-500" />
      default:
        return <Activity className="h-5 w-5 text-gray-500" />
    }
  }

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="card-title">Recent Activity</h3>
      </div>
      <div className="card-content">
        <div className="flow-root">
          <ul className="-mb-8">
            {activities.map((activity, index) => (
              <li key={activity.id}>
                <div className="relative pb-8">
                  {index !== activities.length - 1 && (
                    <span
                      className="absolute top-4 left-4 -ml-px h-full w-0.5 bg-gray-200"
                      aria-hidden="true"
                    />
                  )}
                  <div className="relative flex space-x-3">
                    <div className="flex-shrink-0">
                      {getActivityIcon(activity.type)}
                    </div>
                    <div className="min-w-0 flex-1 pt-1.5 flex justify-between space-x-4">
                      <div>
                        <p className="text-sm text-gray-500">{activity.message}</p>
                        {activity.user && (
                          <p className="text-xs text-gray-400">by {activity.user}</p>
                        )}
                      </div>
                      <div className="text-right text-sm whitespace-nowrap text-gray-500">
                        {new Date(activity.timestamp).toLocaleTimeString()}
                      </div>
                    </div>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  )
}

export default function DashboardPage() {
  const { user } = useAuthStore()

  // Fetch dashboard data
  const { data: healthData } = useQuery(
    'health',
    () => apiHelpers.getDetailedHealth(),
    {
      refetchInterval: 30000, // Refresh every 30 seconds
    }
  )

  const { data: storageData } = useQuery(
    'storage',
    () => apiHelpers.getStorageInfo(),
    {
      refetchInterval: 60000, // Refresh every minute
    }
  )

  // Mock data for demo
  const stats = {
    totalMachines: 24,
    activeSessions: 8,
    totalImages: 12,
    activeTargets: 15,
  }

  const recentActivities: ActivityItem[] = [
    {
      id: '1',
      type: 'session_started',
      message: 'Session started for machine LAB-PC-01',
      timestamp: new Date(Date.now() - 5 * 60 * 1000).toISOString(),
      user: 'admin',
    },
    {
      id: '2',
      type: 'image_uploaded',
      message: 'Windows 11 Pro image uploaded successfully',
      timestamp: new Date(Date.now() - 15 * 60 * 1000).toISOString(),
      user: 'operator1',
    },
    {
      id: '3',
      type: 'machine_created',
      message: 'New machine LAB-PC-25 added to inventory',
      timestamp: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
      user: 'admin',
    },
    {
      id: '4',
      type: 'session_stopped',
      message: 'Session ended for machine LAB-PC-03',
      timestamp: new Date(Date.now() - 45 * 60 * 1000).toISOString(),
      user: 'system',
    },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-1 text-sm text-gray-500">
          Welcome back, {user?.full_name || user?.username}! Here's what's happening with your diskless infrastructure.
        </p>
      </div>

      {/* System Health Alert */}
      {healthData?.data?.status !== 'healthy' && (
        <div className="rounded-md bg-yellow-50 p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <AlertTriangle className="h-5 w-5 text-yellow-400" />
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-yellow-800">
                System Health Warning
              </h3>
              <div className="mt-2 text-sm text-yellow-700">
                <p>Some system components need attention. Check the detailed health status.</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <StatsCard
          title="Total Machines"
          value={stats.totalMachines}
          icon={Monitor}
          trend={{ value: 8, isPositive: true }}
          color="blue"
        />
        <StatsCard
          title="Active Sessions"
          value={stats.activeSessions}
          icon={Activity}
          trend={{ value: 12, isPositive: true }}
          color="green"
        />
        <StatsCard
          title="Disk Images"
          value={stats.totalImages}
          icon={HardDrive}
          trend={{ value: 3, isPositive: false }}
          color="purple"
        />
        <StatsCard
          title="iSCSI Targets"
          value={stats.activeTargets}
          icon={Target}
          trend={{ value: 5, isPositive: true }}
          color="yellow"
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Storage Usage */}
        <div className="lg:col-span-1">
          <div className="card">
            <div className="card-header">
              <h3 className="card-title">Storage Usage</h3>
            </div>
            <div className="card-content">
              <div className="space-y-4">
                {storageData?.data && (
                  <>
                    <div>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-600">Upload Storage</span>
                        <span className="font-medium">
                          {storageData.data.upload_storage.usage_percent.toFixed(1)}%
                        </span>
                      </div>
                      <div className="mt-1 bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full"
                          style={{ width: `${storageData.data.upload_storage.usage_percent}%` }}
                        />
                      </div>
                      <p className="text-xs text-gray-500 mt-1">
                        {storageData.data.upload_storage.free_gb.toFixed(1)} GB free of{' '}
                        {storageData.data.upload_storage.total_gb.toFixed(1)} GB
                      </p>
                    </div>
                    
                    <div>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-600">Images Storage</span>
                        <span className="font-medium">
                          {storageData.data.images_storage.usage_percent.toFixed(1)}%
                        </span>
                      </div>
                      <div className="mt-1 bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-green-600 h-2 rounded-full"
                          style={{ width: `${storageData.data.images_storage.usage_percent}%` }}
                        />
                      </div>
                      <p className="text-xs text-gray-500 mt-1">
                        {storageData.data.images_storage.free_gb.toFixed(1)} GB free of{' '}
                        {storageData.data.images_storage.total_gb.toFixed(1)} GB
                      </p>
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Recent Activity */}
        <div className="lg:col-span-2">
          <ActivityFeed activities={recentActivities} />
        </div>
      </div>

      {/* Quick Actions */}
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">Quick Actions</h3>
          <p className="card-description">Common tasks and shortcuts</p>
        </div>
        <div className="card-content">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <button className="btn btn-primary btn-md">
              <HardDrive className="h-4 w-4 mr-2" />
              Upload Image
            </button>
            <button className="btn btn-secondary btn-md">
              <Monitor className="h-4 w-4 mr-2" />
              Add Machine
            </button>
            <button className="btn btn-secondary btn-md">
              <Target className="h-4 w-4 mr-2" />
              Create Target
            </button>
            <button className="btn btn-secondary btn-md">
              <Activity className="h-4 w-4 mr-2" />
              View Sessions
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

