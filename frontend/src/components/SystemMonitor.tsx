/**
 * SystemMonitor Component
 * Real-time system monitoring with performance metrics and health checks
 */

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { 
  Activity, 
  Cpu, 
  MemoryStick, 
  AlertCircle,
  CheckCircle,
  Clock,
  RefreshCw,
  Loader2
} from 'lucide-react';
import { toast } from 'react-hot-toast';
// Optimized imports for better tree-shaking
import { LineChart } from 'recharts/es6/chart/LineChart';
import { Line } from 'recharts/es6/cartesian/Line';
import { XAxis } from 'recharts/es6/cartesian/XAxis';
import { YAxis } from 'recharts/es6/cartesian/YAxis';
import { CartesianGrid } from 'recharts/es6/cartesian/CartesianGrid';
import { Tooltip } from 'recharts/es6/component/Tooltip';
import { ResponsiveContainer } from 'recharts/es6/component/ResponsiveContainer';
import { AreaChart } from 'recharts/es6/chart/AreaChart';
import { Area } from 'recharts/es6/cartesian/Area';

import { Button } from './ui/Button';
import { Card } from './ui/Card';
import { StatusBadge } from './ui/StatusBadge';
import { ProgressBar } from './ui/ProgressBar';
import { api } from '../lib/api';

// interface SystemMetrics { // Unused for now
//   timestamp: string;
//   cpu_usage: number;
//   memory_usage: number;
//   disk_usage: number;
//   network_in: number;
//   network_out: number;
//   active_sessions: number;
//   total_requests: number;
//   error_rate: number;
// }

interface ServiceStatus {
  name: string;
  status: 'RUNNING' | 'STOPPED' | 'ERROR' | 'WARNING';
  uptime: string;
  last_check: string;
  health_score: number;
  dependencies: string[];
}

interface StorageInfo {
  path: string;
  total_space: number;
  used_space: number;
  free_space: number;
  usage_percentage: number;
  filesystem_type: string;
}

interface NetworkInterface {
  name: string;
  status: 'UP' | 'DOWN';
  ip_address: string;
  mac_address: string;
  bytes_sent: number;
  bytes_received: number;
  packets_sent: number;
  packets_received: number;
}

// interface SystemHealth { // Unused for now
//   overall_status: 'HEALTHY' | 'WARNING' | 'CRITICAL';
//   health_score: number;
//   issues: Array<{
//     severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
//     component: string;
//     message: string;
//     timestamp: string;
//   }>;
//   recommendations: string[];
// }

const SystemMonitor: React.FC = () => {
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(5000);
  const [timeRange, setTimeRange] = useState('1h');
  const [selectedMetric, setSelectedMetric] = useState('cpu_usage');

  // Fetch system metrics
  const { data: metricsData, isLoading: metricsLoading, refetch: refetchMetrics } = useQuery({
    queryKey: ['system-metrics', timeRange],
    queryFn: () => api.get(`/api/v1/monitoring/metrics?range=${timeRange}`).then(res => res.data),
    refetchInterval: autoRefresh ? refreshInterval : false,
  });

  // Fetch service status
  const { data: servicesData, isLoading: servicesLoading, refetch: refetchServices } = useQuery({
    queryKey: ['service-status'],
    queryFn: () => api.get('/api/v1/monitoring/services').then(res => res.data),
    refetchInterval: autoRefresh ? refreshInterval : false,
  });

  // Fetch storage info
  const { data: storageData, isLoading: storageLoading, refetch: refetchStorage } = useQuery({
    queryKey: ['storage-info'],
    queryFn: () => api.get('/api/v1/monitoring/storage').then(res => res.data),
    refetchInterval: autoRefresh ? refreshInterval * 2 : false, // Less frequent
  });

  // Fetch network interfaces
  const { data: networkData, isLoading: networkLoading, refetch: refetchNetwork } = useQuery({
    queryKey: ['network-interfaces'],
    queryFn: () => api.get('/api/v1/monitoring/network').then(res => res.data),
    refetchInterval: autoRefresh ? refreshInterval : false,
  });

  // Fetch system health
  const { data: healthData, isLoading: healthLoading, refetch: refetchHealth } = useQuery({
    queryKey: ['system-health'],
    queryFn: () => api.get('/api/v1/monitoring/health').then(res => res.data),
    refetchInterval: autoRefresh ? refreshInterval : false,
  });

  const metrics = metricsData?.metrics || [];
  const services = servicesData?.services || [];
  const storage = storageData?.storage || [];
  const network = networkData?.interfaces || [];
  const health = healthData || { overall_status: 'HEALTHY', health_score: 100, issues: [], recommendations: [] };

  const handleRefresh = () => {
    refetchMetrics();
    refetchServices();
    refetchStorage();
    refetchNetwork();
    refetchHealth();
    toast.success('System data refreshed');
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'RUNNING':
      case 'UP':
      case 'HEALTHY':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'WARNING':
        return <AlertCircle className="w-4 h-4 text-yellow-500" />;
      case 'STOPPED':
      case 'DOWN':
      case 'ERROR':
      case 'CRITICAL':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      default:
        return <Clock className="w-4 h-4 text-gray-500" />;
    }
  };

  const getHealthColor = (score: number) => {
    if (score >= 90) return 'text-green-600';
    if (score >= 70) return 'text-yellow-600';
    if (score >= 50) return 'text-orange-600';
    return 'text-red-600';
  };

  const formatBytes = (bytes: number) => {
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    if (bytes === 0) return '0 B';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${sizes[i]}`;
  };

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const formatUptime = (uptime: string) => {
    // Parse uptime string and format it nicely
    return uptime;
  };

  const getCurrentMetricValue = () => {
    if (metrics.length === 0) return 0;
    const latest = metrics[metrics.length - 1];
    return latest[selectedMetric] || 0;
  };

  // const getMetricTrend = () => { // Unused for now
  //   if (metrics.length < 2) return 'stable';
  //   const latest = metrics[metrics.length - 1][selectedMetric];
  //   const previous = metrics[metrics.length - 2][selectedMetric];
  //   if (latest > previous) return 'up';
  //   if (latest < previous) return 'down';
  //   return 'stable';
  // };

  // const getMetricIcon = (metric: string) => { // Unused for now
  //   switch (metric) {
  //     case 'cpu_usage':
  //       return <Cpu className="w-4 h-4" />;
  //     case 'memory_usage':
  //       return <MemoryStick className="w-4 h-4" />;
  //     case 'disk_usage':
  //       return <HardDrive className="w-4 h-4" />;
  //     case 'network_in':
  //     case 'network_out':
  //       return <Wifi className="w-4 h-4" />;
  //     case 'active_sessions':
  //       return <Activity className="w-4 h-4" />;
  //     default:
  //       return <Server className="w-4 h-4" />;
  //   }
  // };

  if (metricsLoading || servicesLoading || storageLoading || networkLoading || healthLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
        <span className="ml-2 text-gray-600">Loading system data...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">System Monitor</h2>
          <p className="text-gray-600">Real-time system performance and health monitoring</p>
        </div>
        <div className="flex items-center space-x-3">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="15m">Last 15 minutes</option>
            <option value="1h">Last hour</option>
            <option value="6h">Last 6 hours</option>
            <option value="24h">Last 24 hours</option>
            <option value="7d">Last 7 days</option>
          </select>
          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              id="auto-refresh"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <label htmlFor="auto-refresh" className="text-sm text-gray-700">
              Auto-refresh
            </label>
          </div>
          <select
            value={refreshInterval}
            onChange={(e) => setRefreshInterval(parseInt(e.target.value))}
            className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value={2000}>2s</option>
            <option value={5000}>5s</option>
            <option value={10000}>10s</option>
            <option value={30000}>30s</option>
          </select>
          <Button
            onClick={handleRefresh}
            variant="outline"
            className="flex items-center space-x-2"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Refresh</span>
          </Button>
        </div>
      </div>

      {/* System Health Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">System Health</p>
              <p className={`text-2xl font-bold ${getHealthColor(health.health_score)}`}>
                {health.health_score}%
              </p>
            </div>
            {getStatusIcon(health.overall_status)}
          </div>
        </Card>
        
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Active Sessions</p>
              <p className="text-2xl font-bold text-blue-600">
                {getCurrentMetricValue()}
              </p>
            </div>
            <Activity className="w-8 h-8 text-blue-500" />
          </div>
        </Card>
        
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">CPU Usage</p>
              <p className="text-2xl font-bold text-purple-600">
                {metrics.length > 0 ? `${metrics[metrics.length - 1].cpu_usage.toFixed(1)}%` : '0%'}
              </p>
            </div>
            <Cpu className="w-8 h-8 text-purple-500" />
          </div>
        </Card>
        
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Memory Usage</p>
              <p className="text-2xl font-bold text-green-600">
                {metrics.length > 0 ? `${metrics[metrics.length - 1].memory_usage.toFixed(1)}%` : '0%'}
              </p>
            </div>
            <MemoryStick className="w-8 h-8 text-green-500" />
          </div>
        </Card>
      </div>

      {/* Performance Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* CPU and Memory Usage */}
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">CPU & Memory Usage</h3>
            <div className="flex space-x-2">
              <Button
                onClick={() => setSelectedMetric('cpu_usage')}
                variant={selectedMetric === 'cpu_usage' ? 'primary' : 'outline'}
                size="sm"
              >
                CPU
              </Button>
              <Button
                onClick={() => setSelectedMetric('memory_usage')}
                variant={selectedMetric === 'memory_usage' ? 'primary' : 'outline'}
                size="sm"
              >
                Memory
              </Button>
            </div>
          </div>
          
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={metrics}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="timestamp" 
                  tickFormatter={(value) => new Date(value).toLocaleTimeString()}
                />
                <YAxis domain={[0, 100]} />
                <Tooltip 
                  labelFormatter={(value) => new Date(value).toLocaleString()}
                  formatter={(value) => [`${value}%`, selectedMetric.replace('_', ' ').toUpperCase()]}
                />
                <Area 
                  type="monotone" 
                  dataKey={selectedMetric} 
                  stroke="#3B82F6" 
                  fill="#3B82F6" 
                  fillOpacity={0.3}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Network Activity */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Network Activity</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={metrics}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="timestamp" 
                  tickFormatter={(value) => new Date(value).toLocaleTimeString()}
                />
                <YAxis />
                <Tooltip 
                  labelFormatter={(value) => new Date(value).toLocaleString()}
                  formatter={(value: number | string, name: string) => [formatBytes(Number(value)), name]}
                />
                <Line 
                  type="monotone" 
                  dataKey="network_in" 
                  stroke="#10B981" 
                  strokeWidth={2}
                  name="In"
                />
                <Line 
                  type="monotone" 
                  dataKey="network_out" 
                  stroke="#F59E0B" 
                  strokeWidth={2}
                  name="Out"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      {/* Services Status */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Services Status</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {services.map((service: ServiceStatus) => (
            <div key={service.name} className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-2">
                  {getStatusIcon(service.status)}
                  <span className="font-medium text-gray-900">{service.name}</span>
                </div>
                <StatusBadge status={service.status} text={service.status} />
              </div>
              <div className="space-y-1 text-sm text-gray-600">
                <p>Uptime: {formatUptime(service.uptime)}</p>
                <p>Health: {service.health_score}%</p>
                <p>Last check: {formatDateTime(service.last_check)}</p>
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Storage Information */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Storage Information</h3>
        <div className="space-y-4">
          {storage.map((storage: StorageInfo) => (
            <div key={storage.path} className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <div>
                  <h4 className="font-medium text-gray-900">{storage.path}</h4>
                  <p className="text-sm text-gray-500">{storage.filesystem_type}</p>
                </div>
                <span className="text-sm font-medium text-gray-900">
                  {storage.usage_percentage.toFixed(1)}%
                </span>
              </div>
              <ProgressBar progress={storage.usage_percentage} className="mb-2" />
              <div className="flex justify-between text-sm text-gray-600">
                <span>Used: {formatBytes(storage.used_space)}</span>
                <span>Free: {formatBytes(storage.free_space)}</span>
                <span>Total: {formatBytes(storage.total_space)}</span>
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Network Interfaces */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Network Interfaces</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Interface
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  IP Address
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  MAC Address
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Bytes Sent
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Bytes Received
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {network.map((iface: NetworkInterface) => (
                <tr key={iface.name} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {iface.name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      {getStatusIcon(iface.status)}
                      <StatusBadge status={iface.status} text={iface.status} className="ml-2" />
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {iface.ip_address}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 font-mono">
                    {iface.mac_address}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {formatBytes(iface.bytes_sent)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {formatBytes(iface.bytes_received)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* System Issues and Recommendations */}
      {(health.issues.length > 0 || health.recommendations.length > 0) && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Issues */}
          {health.issues.length > 0 && (
            <Card className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">System Issues</h3>
              <div className="space-y-3">
                {health.issues.map((issue: { severity: string; message: string; component?: string; timestamp?: string }, index: number) => (
                  <div key={index} className="border border-gray-200 rounded-lg p-3">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium text-gray-900">{issue.component}</span>
                      <StatusBadge status={issue.severity} text={issue.severity} />
                    </div>
                    <p className="text-sm text-gray-600">{issue.message}</p>
                    {issue.timestamp && (
                      <p className="text-xs text-gray-500 mt-1">
                        {formatDateTime(issue.timestamp)}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Recommendations */}
          {health.recommendations.length > 0 && (
            <Card className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Recommendations</h3>
              <div className="space-y-2">
                {health.recommendations.map((recommendation: string | { priority: string; action: string; impact: string }, index: number) => (
                  <div key={index} className="flex items-start space-x-2">
                    <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                    <p className="text-sm text-gray-600">{typeof recommendation === 'string' ? recommendation : recommendation.action}</p>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </div>
      )}
    </div>
  );
};

export default SystemMonitor;
