/**
 * SessionManager Component
 * Manages diskless boot sessions with real-time status updates
 */

import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  Play, 
  Square, 
  RefreshCw, 
  Monitor, 
  HardDrive, 
  Clock, 
  AlertCircle,
  CheckCircle,
  XCircle,
  Loader2
} from 'lucide-react';
import { toast } from 'react-hot-toast';

import { Button } from './ui/Button';
import { Card } from './ui/Card';
import { StatusBadge } from './ui/StatusBadge';
import { ProgressBar } from './ui/ProgressBar';
import { useAuthStore } from '../stores/authStore';
import { api } from '../lib/api';

interface Session {
  id: number;
  machine_id: number;
  target_id: number;
  image_id: number;
  session_type: 'DISKLESS_BOOT' | 'MAINTENANCE' | 'TESTING';
  status: 'ACTIVE' | 'STOPPED' | 'ERROR' | 'PENDING';
  description?: string;
  started_at: string;
  ended_at?: string;
  duration_seconds?: number;
  created_by: number;
}

interface Machine {
  id: number;
  name: string;
  mac_address: string;
  ip_address: string;
  status: 'ACTIVE' | 'INACTIVE' | 'MAINTENANCE';
  boot_mode: 'bios' | 'uefi';
  description?: string;
}

interface Image {
  id: number;
  name: string;
  filename: string;
  format: 'VHDX' | 'RAW' | 'QCOW2';
  status: 'READY' | 'PROCESSING' | 'ERROR' | 'UPLOADING';
  size_bytes: number;
  description?: string;
}

interface SessionStartRequest {
  machine_id: number;
  image_id: number;
  session_type: 'DISKLESS_BOOT' | 'MAINTENANCE' | 'TESTING';
  description?: string;
}

interface SessionStartResponse {
  session: Session;
  target_info: {
    target_id: string;
    iqn: string;
    initiator_iqn: string;
    portal_ip: string;
    portal_port: number;
    lun_id: number;
  };
  boot_script: string;
  ipxe_script_url: string;
  iscsi_details: {
    target_iqn: string;
    initiator_iqn: string;
    portal_ip: string;
    portal_port: number;
    lun_id: number;
  };
}

const SessionManager: React.FC = () => {
  const [selectedMachine, setSelectedMachine] = useState<Machine | null>(null);
  const [selectedImage, setSelectedImage] = useState<Image | null>(null);
  const [sessionType, setSessionType] = useState<'DISKLESS_BOOT' | 'MAINTENANCE' | 'TESTING'>('DISKLESS_BOOT');
  const [description, setDescription] = useState('');
  const [isStarting, setIsStarting] = useState(false);

  const { user } = useAuthStore();
  const queryClient = useQueryClient();

  // Fetch sessions
  const { data: sessionsData, isLoading: sessionsLoading, refetch: refetchSessions } = useQuery({
    queryKey: ['sessions'],
    queryFn: () => api.get('/api/v1/sessions/').then(res => res.data),
    refetchInterval: 5000, // Refresh every 5 seconds
  });

  // Fetch machines
  const { data: machinesData, isLoading: machinesLoading } = useQuery({
    queryKey: ['machines'],
    queryFn: () => api.get('/machines/').then(res => res.data),
  });

  // Fetch images
  const { data: imagesData, isLoading: imagesLoading } = useQuery({
    queryKey: ['images'],
    queryFn: () => api.get('/images/').then(res => res.data),
  });

  // Start session mutation
  const startSessionMutation = useMutation({
    mutationFn: (data: SessionStartRequest) => 
      api.post('/api/v1/sessions/start', data).then(res => res.data as SessionStartResponse),
    onSuccess: (data) => {
      toast.success(`Session started successfully for ${selectedMachine?.name}`);
      queryClient.invalidateQueries({ queryKey: ['sessions'] });
      queryClient.invalidateQueries({ queryKey: ['machines'] });
      setIsStarting(false);
      
      // Show session details
      console.log('Session started:', data);
    },
    onError: (error: any) => {
      toast.error(`Failed to start session: ${error.response?.data?.detail || error.message}`);
      setIsStarting(false);
    },
  });

  // Stop session mutation
  const stopSessionMutation = useMutation({
    mutationFn: (sessionId: number) => 
      api.post(`/api/v1/sessions/${sessionId}/stop`).then(res => res.data),
    onSuccess: (data, sessionId) => {
      toast.success(`Session ${sessionId} stopped successfully`);
      queryClient.invalidateQueries({ queryKey: ['sessions'] });
      queryClient.invalidateQueries({ queryKey: ['machines'] });
    },
    onError: (error: any) => {
      toast.error(`Failed to stop session: ${error.response?.data?.detail || error.message}`);
    },
  });

  // Get session statistics
  const { data: statsData } = useQuery({
    queryKey: ['session-stats'],
    queryFn: () => api.get('/api/v1/sessions/stats').then(res => res.data),
    refetchInterval: 10000, // Refresh every 10 seconds
  });

  const sessions = sessionsData?.sessions || [];
  const machines = machinesData?.machines || [];
  const images = imagesData?.images || [];
  const stats = statsData || { total_sessions: 0, active_sessions: 0, status_counts: {} };

  const handleStartSession = async () => {
    if (!selectedMachine || !selectedImage) {
      toast.error('Please select both a machine and an image');
      return;
    }

    setIsStarting(true);
    startSessionMutation.mutate({
      machine_id: selectedMachine.id,
      image_id: selectedImage.id,
      session_type: sessionType,
      description: description || undefined,
    });
  };

  const handleStopSession = (sessionId: number) => {
    if (window.confirm('Are you sure you want to stop this session?')) {
      stopSessionMutation.mutate(sessionId);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'ACTIVE':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'STOPPED':
        return <XCircle className="w-4 h-4 text-gray-500" />;
      case 'ERROR':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      case 'PENDING':
        return <Loader2 className="w-4 h-4 text-yellow-500 animate-spin" />;
      default:
        return <Clock className="w-4 h-4 text-gray-500" />;
    }
  };

  const getSessionTypeIcon = (type: string) => {
    switch (type) {
      case 'DISKLESS_BOOT':
        return <HardDrive className="w-4 h-4" />;
      case 'MAINTENANCE':
        return <Monitor className="w-4 h-4" />;
      case 'TESTING':
        return <AlertCircle className="w-4 h-4" />;
      default:
        return <Monitor className="w-4 h-4" />;
    }
  };

  const formatDuration = (seconds?: number) => {
    if (!seconds) return 'N/A';
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${hours}h ${minutes}m ${secs}s`;
  };

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  if (sessionsLoading || machinesLoading || imagesLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
        <span className="ml-2 text-gray-600">Loading session data...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Session Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Sessions</p>
              <p className="text-2xl font-bold text-gray-900">{stats.total_sessions}</p>
            </div>
            <Monitor className="w-8 h-8 text-blue-500" />
          </div>
        </Card>
        
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Active Sessions</p>
              <p className="text-2xl font-bold text-green-600">{stats.active_sessions}</p>
            </div>
            <CheckCircle className="w-8 h-8 text-green-500" />
          </div>
        </Card>
        
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Stopped Sessions</p>
              <p className="text-2xl font-bold text-gray-600">{stats.status_counts?.STOPPED || 0}</p>
            </div>
            <XCircle className="w-8 h-8 text-gray-500" />
          </div>
        </Card>
        
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Error Sessions</p>
              <p className="text-2xl font-bold text-red-600">{stats.status_counts?.ERROR || 0}</p>
            </div>
            <AlertCircle className="w-8 h-8 text-red-500" />
          </div>
        </Card>
      </div>

      {/* Start New Session */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Start New Session</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          {/* Machine Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Machine
            </label>
            <select
              value={selectedMachine?.id || ''}
              onChange={(e) => {
                const machine = machines.find((m: any) => m.id === parseInt(e.target.value));
                setSelectedMachine(machine || null);
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Choose a machine...</option>
              {machines
                .filter((m: any) => m.status === 'ACTIVE')
                .map((machine: any) => (
                  <option key={machine.id} value={machine.id}>
                    {machine.name} ({machine.mac_address}) - {machine.ip_address}
                  </option>
                ))}
            </select>
          </div>

          {/* Image Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Image
            </label>
            <select
              value={selectedImage?.id || ''}
              onChange={(e) => {
                const image = images.find((i: any) => i.id === parseInt(e.target.value));
                setSelectedImage(image || null);
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Choose an image...</option>
              {images
                .filter((i: any) => i.status === 'READY')
                .map((image: any) => (
                  <option key={image.id} value={image.id}>
                    {image.name} ({image.format}) - {(image.size_bytes / 1024 / 1024 / 1024).toFixed(1)}GB
                  </option>
                ))}
            </select>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          {/* Session Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Session Type
            </label>
            <select
              value={sessionType}
              onChange={(e) => setSessionType(e.target.value as any)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="DISKLESS_BOOT">Diskless Boot</option>
              <option value="MAINTENANCE">Maintenance</option>
              <option value="TESTING">Testing</option>
            </select>
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Description (Optional)
            </label>
            <input
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Session description..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        <div className="flex justify-end">
          <Button
            onClick={handleStartSession}
            disabled={!selectedMachine || !selectedImage || isStarting}
            className="flex items-center space-x-2"
          >
            {isStarting ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Play className="w-4 h-4" />
            )}
            <span>{isStarting ? 'Starting...' : 'Start Session'}</span>
          </Button>
        </div>
      </Card>

      {/* Active Sessions */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Active Sessions</h3>
          <Button
            onClick={() => refetchSessions()}
            variant="outline"
            size="sm"
            className="flex items-center space-x-2"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Refresh</span>
          </Button>
        </div>

        {sessions.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <Monitor className="w-12 h-12 mx-auto mb-4 text-gray-300" />
            <p>No sessions found</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Session
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Machine
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Image
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Duration
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Started
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {sessions.map((session: any) => {
                  const machine = machines.find((m: any) => m.id === session.machine_id);
                  const image = images.find((i: any) => i.id === session.image_id);
                  
                  return (
                    <tr key={session.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          {getSessionTypeIcon(session.session_type)}
                          <div className="ml-3">
                            <div className="text-sm font-medium text-gray-900">
                              Session #{session.id}
                            </div>
                            <div className="text-sm text-gray-500">
                              {session.session_type.replace('_', ' ')}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">{machine?.name || 'Unknown'}</div>
                        <div className="text-sm text-gray-500">{machine?.mac_address || 'N/A'}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">{image?.name || 'Unknown'}</div>
                        <div className="text-sm text-gray-500">{image?.format || 'N/A'}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          {getStatusIcon(session.status)}
                          <StatusBadge status={session.status} text={session.status} className="ml-2" />
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {formatDuration(session.duration_seconds)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {formatDateTime(session.started_at)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        {session.status === 'ACTIVE' && (
                          <Button
                            onClick={() => handleStopSession(session.id)}
                            variant="outline"
                            size="sm"
                            className="flex items-center space-x-1 text-red-600 hover:text-red-700"
                          >
                            <Square className="w-4 h-4" />
                            <span>Stop</span>
                          </Button>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
};

export default SessionManager;
