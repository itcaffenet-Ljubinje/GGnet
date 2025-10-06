/**
 * NetworkBootMonitor Component
 * Real-time monitoring of network boot processes and PXE/iPXE status
 */

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { 
  Wifi, 
  WifiOff, 
  Monitor, 
  HardDrive, 
  AlertCircle,
  CheckCircle,
  Clock,
  RefreshCw,
  Activity,
  Server,
  Globe,
  Loader2
} from 'lucide-react';
import { toast } from 'react-hot-toast';

import { Button } from './ui/Button';
import { Card } from './ui/Card';
import { StatusBadge } from './ui/StatusBadge';
import { ProgressBar } from './ui/ProgressBar';
import { api } from '../lib/api';

interface BootEvent {
  id: string;
  timestamp: string;
  machine_mac: string;
  machine_ip?: string;
  event_type: 'DHCP_REQUEST' | 'TFTP_REQUEST' | 'IPXE_LOAD' | 'ISCSI_CONNECT' | 'BOOT_SUCCESS' | 'BOOT_FAILED';
  status: 'SUCCESS' | 'FAILED' | 'IN_PROGRESS';
  message: string;
  details?: Record<string, any>;
}

interface NetworkService {
  name: string;
  status: 'RUNNING' | 'STOPPED' | 'ERROR';
  port?: number;
  last_check: string;
  uptime?: string;
}

interface BootStatistics {
  total_boots: number;
  successful_boots: number;
  failed_boots: number;
  success_rate: number;
  average_boot_time: number;
  last_24h_boots: number;
  active_sessions: number;
}

interface MachineBootStatus {
  machine_id: number;
  machine_name: string;
  mac_address: string;
  ip_address: string;
  boot_status: 'IDLE' | 'BOOTING' | 'SUCCESS' | 'FAILED';
  last_boot_time?: string;
  boot_duration?: number;
  current_session_id?: number;
}

const NetworkBootMonitor: React.FC = () => {
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(5000);

  // Fetch boot events
  const { data: bootEventsData, isLoading: eventsLoading, refetch: refetchEvents } = useQuery({
    queryKey: ['boot-events'],
    queryFn: () => api.get('/api/v1/monitoring/boot-events').then(res => res.data),
    refetchInterval: autoRefresh ? refreshInterval : false,
  });

  // Fetch network services status
  const { data: servicesData, isLoading: servicesLoading, refetch: refetchServices } = useQuery({
    queryKey: ['network-services'],
    queryFn: () => api.get('/api/v1/monitoring/network-services').then(res => res.data),
    refetchInterval: autoRefresh ? refreshInterval : false,
  });

  // Fetch boot statistics
  const { data: statsData, isLoading: statsLoading, refetch: refetchStats } = useQuery({
    queryKey: ['boot-statistics'],
    queryFn: () => api.get('/api/v1/monitoring/boot-statistics').then(res => res.data),
    refetchInterval: autoRefresh ? refreshInterval : false,
  });

  // Fetch machine boot status
  const { data: machinesData, isLoading: machinesLoading, refetch: refetchMachines } = useQuery({
    queryKey: ['machine-boot-status'],
    queryFn: () => api.get('/api/v1/monitoring/machine-boot-status').then(res => res.data),
    refetchInterval: autoRefresh ? refreshInterval : false,
  });

  const bootEvents = bootEventsData?.events || [];
  const services = servicesData?.services || [];
  const stats = statsData || {};
  const machines = machinesData?.machines || [];

  const handleRefresh = () => {
    refetchEvents();
    refetchServices();
    refetchStats();
    refetchMachines();
    toast.success('Network boot data refreshed');
  };

  const getEventIcon = (eventType: string) => {
    switch (eventType) {
      case 'DHCP_REQUEST':
        return <Globe className="w-4 h-4 text-blue-500" />;
      case 'TFTP_REQUEST':
        return <Server className="w-4 h-4 text-green-500" />;
      case 'IPXE_LOAD':
        return <Monitor className="w-4 h-4 text-purple-500" />;
      case 'ISCSI_CONNECT':
        return <HardDrive className="w-4 h-4 text-orange-500" />;
      case 'BOOT_SUCCESS':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'BOOT_FAILED':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      default:
        return <Activity className="w-4 h-4 text-gray-500" />;
    }
  };

  const getEventStatusIcon = (status: string) => {
    switch (status) {
      case 'SUCCESS':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'FAILED':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      case 'IN_PROGRESS':
        return <Loader2 className="w-4 h-4 text-yellow-500 animate-spin" />;
      default:
        return <Clock className="w-4 h-4 text-gray-500" />;
    }
  };

  const getServiceStatusIcon = (status: string) => {
    switch (status) {
      case 'RUNNING':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'STOPPED':
        return <WifiOff className="w-4 h-4 text-red-500" />;
      case 'ERROR':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      default:
        return <Wifi className="w-4 h-4 text-gray-500" />;
    }
  };

  const getBootStatusIcon = (status: string) => {
    switch (status) {
      case 'IDLE':
        return <Clock className="w-4 h-4 text-gray-500" />;
      case 'BOOTING':
        return <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />;
      case 'SUCCESS':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'FAILED':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      default:
        return <Activity className="w-4 h-4 text-gray-500" />;
    }
  };

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const formatDuration = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes}m ${secs}s`;
  };

  const formatEventType = (eventType: string) => {
    return eventType.replace(/_/g, ' ').toLowerCase().replace(/\b\w/g, l => l.toUpperCase());
  };

  if (eventsLoading || servicesLoading || statsLoading || machinesLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
        <span className="ml-2 text-gray-600">Loading network boot data...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Network Boot Monitor</h2>
          <p className="text-gray-600">Real-time monitoring of PXE/iPXE boot processes</p>
        </div>
        <div className="flex items-center space-x-3">
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

      {/* Boot Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Boots</p>
              <p className="text-2xl font-bold text-gray-900">{stats.total_boots || 0}</p>
            </div>
            <Activity className="w-8 h-8 text-blue-500" />
          </div>
        </Card>
        
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Success Rate</p>
              <p className="text-2xl font-bold text-green-600">
                {stats.success_rate ? `${stats.success_rate.toFixed(1)}%` : '0%'}
              </p>
            </div>
            <CheckCircle className="w-8 h-8 text-green-500" />
          </div>
        </Card>
        
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Avg Boot Time</p>
              <p className="text-2xl font-bold text-purple-600">
                {stats.average_boot_time ? formatDuration(stats.average_boot_time) : 'N/A'}
              </p>
            </div>
            <Clock className="w-8 h-8 text-purple-500" />
          </div>
        </Card>
        
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Active Sessions</p>
              <p className="text-2xl font-bold text-orange-600">{stats.active_sessions || 0}</p>
            </div>
            <Monitor className="w-8 h-8 text-orange-500" />
          </div>
        </Card>
      </div>

      {/* Network Services Status */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Network Services</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {services.map((service: NetworkService) => (
            <div key={service.name} className="flex items-center justify-between p-3 border border-gray-200 rounded-lg">
              <div className="flex items-center space-x-3">
                {getServiceStatusIcon(service.status)}
                <div>
                  <p className="font-medium text-gray-900">{service.name}</p>
                  {service.port && (
                    <p className="text-sm text-gray-500">Port: {service.port}</p>
                  )}
                </div>
              </div>
              <div className="text-right">
                <StatusBadge status={service.status} text={service.status} />
                {service.uptime && (
                  <p className="text-xs text-gray-500 mt-1">Uptime: {service.uptime}</p>
                )}
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Machine Boot Status */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Machine Boot Status</h3>
        
        {machines.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <Monitor className="w-12 h-12 mx-auto mb-4 text-gray-300" />
            <p>No machines found</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Machine
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Network
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Boot Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Last Boot
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Duration
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Session
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {machines.map((machine: MachineBootStatus) => (
                  <tr key={machine.machine_id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">
                        {machine.machine_name}
                      </div>
                      <div className="text-sm text-gray-500">
                        ID: {machine.machine_id}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{machine.mac_address}</div>
                      <div className="text-sm text-gray-500">{machine.ip_address}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        {getBootStatusIcon(machine.boot_status)}
                        <StatusBadge status={machine.boot_status} text={machine.boot_status} className="ml-2" />
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {machine.last_boot_time ? formatDateTime(machine.last_boot_time) : 'Never'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {machine.boot_duration ? formatDuration(machine.boot_duration) : 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {machine.current_session_id ? `#${machine.current_session_id}` : 'None'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Recent Boot Events */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Boot Events</h3>
        
        {bootEvents.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <Activity className="w-12 h-12 mx-auto mb-4 text-gray-300" />
            <p>No boot events found</p>
          </div>
        ) : (
          <div className="space-y-3">
            {bootEvents.slice(0, 20).map((event: BootEvent) => (
              <div key={event.id} className="flex items-center justify-between p-3 border border-gray-200 rounded-lg hover:bg-gray-50">
                <div className="flex items-center space-x-3">
                  {getEventIcon(event.event_type)}
                  <div>
                    <p className="font-medium text-gray-900">
                      {formatEventType(event.event_type)}
                    </p>
                    <p className="text-sm text-gray-500">
                      {event.machine_mac} {event.machine_ip && `(${event.machine_ip})`}
                    </p>
                    <p className="text-sm text-gray-600">{event.message}</p>
                  </div>
                </div>
                <div className="text-right">
                  <div className="flex items-center space-x-2">
                    {getEventStatusIcon(event.status)}
                    <StatusBadge status={event.status} text={event.status} />
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    {formatDateTime(event.timestamp)}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
};

export default NetworkBootMonitor;
