/**
 * TargetManager Component
 * Manages iSCSI targets with real-time status and configuration
 */

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  Plus, 
  Trash2, 
  RefreshCw, 
  HardDrive, 
  Monitor, 
  Settings,
  AlertCircle,
  CheckCircle,
  XCircle,
  Loader2,
  Copy,
  ExternalLink
} from 'lucide-react';
import { toast } from 'react-hot-toast';

import { Button } from './ui/Button';
import { Card } from './ui/Card';
import { StatusBadge } from './ui/StatusBadge';
import { useAuthStore } from '../stores/authStore';
import { api } from '../lib/api';

interface Target {
  id: number;
  target_id: string;
  iqn: string;
  machine_id: number;
  image_id: number;
  created_by: number;
  image_path: string;
  initiator_iqn: string;
  lun_id: number;
  status: 'ACTIVE' | 'INACTIVE' | 'ERROR' | 'PENDING';
  description?: string;
  created_at: string;
  updated_at: string;
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

interface ImageData {
  id: number;
  name: string;
  filename: string;
  format: 'VHDX' | 'RAW' | 'QCOW2';
  status: 'READY' | 'PROCESSING' | 'ERROR' | 'UPLOADING';
  size_bytes: number;
  description?: string;
}

interface TargetCreateRequest {
  machine_id: number;
  image_id: number;
  description?: string;
  lun_id?: number;
  initiator_iqn?: string;
}

interface TargetUpdateRequest {
  description?: string;
  status?: 'ACTIVE' | 'INACTIVE' | 'ERROR' | 'PENDING';
  lun_id?: number;
  initiator_iqn?: string;
}

const TargetManager: React.FC = () => {
  const [selectedMachine, setSelectedMachine] = useState<Machine | null>(null);
  const [selectedImage, setSelectedImage] = useState<Image | null>(null);
  const [description, setDescription] = useState('');
  const [lunId, setLunId] = useState(0);
  const [initiatorIqn, setInitiatorIqn] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const [showCreateForm, setShowCreateForm] = useState(false);

  // const { user } = useAuthStore(); // Unused for now
  const queryClient = useQueryClient();

  // Fetch targets
  const { data: targetsData, isLoading: targetsLoading, refetch: refetchTargets } = useQuery({
    queryKey: ['targets'],
    queryFn: () => api.get('/api/v1/targets/').then(res => res.data),
    refetchInterval: 10000, // Refresh every 10 seconds
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

  // Create target mutation
  const createTargetMutation = useMutation({
    mutationFn: (data: TargetCreateRequest) => 
      api.post('/api/v1/targets/', data).then(res => res.data as Target),
    onSuccess: (data) => {
      toast.success(`iSCSI target created successfully for ${selectedMachine?.name}`);
      queryClient.invalidateQueries({ queryKey: ['targets'] });
      queryClient.invalidateQueries({ queryKey: ['machines'] });
      setIsCreating(false);
      setShowCreateForm(false);
      resetForm();
    },
    onError: (error: any) => {
      toast.error(`Failed to create target: ${error.response?.data?.detail || error.message}`);
      setIsCreating(false);
    },
  });

  // Update target mutation
  const updateTargetMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: TargetUpdateRequest }) => 
      api.put(`/api/v1/targets/${id}`, data).then(res => res.data as Target),
    onSuccess: (data) => {
      toast.success(`Target ${data.target_id} updated successfully`);
      queryClient.invalidateQueries({ queryKey: ['targets'] });
    },
    onError: (error: any) => {
      toast.error(`Failed to update target: ${error.response?.data?.detail || error.message}`);
    },
  });

  // Delete target mutation
  const deleteTargetMutation = useMutation({
    mutationFn: (id: number) => 
      api.delete(`/api/v1/targets/${id}`).then(res => res.data),
    onSuccess: (data, id) => {
      toast.success(`Target ${id} deleted successfully`);
      queryClient.invalidateQueries({ queryKey: ['targets'] });
      queryClient.invalidateQueries({ queryKey: ['machines'] });
    },
    onError: (error: any) => {
      toast.error(`Failed to delete target: ${error.response?.data?.detail || error.message}`);
    },
  });

  const targets = targetsData || [];
  const machines = machinesData?.machines || [];
  const images = imagesData?.images || [];

  const resetForm = () => {
    setSelectedMachine(null);
    setSelectedImage(null);
    setDescription('');
    setLunId(0);
    setInitiatorIqn('');
  };

  const handleCreateTarget = async () => {
    if (!selectedMachine || !selectedImage) {
      toast.error('Please select both a machine and an image');
      return;
    }

    setIsCreating(true);
    createTargetMutation.mutate({
      machine_id: selectedMachine.id,
      image_id: selectedImage.id,
      description: description || undefined,
      lun_id: lunId,
      initiator_iqn: initiatorIqn || undefined,
    });
  };

  const handleDeleteTarget = (targetId: number, targetIqn: string) => {
    if (window.confirm(`Are you sure you want to delete target ${targetIqn}?`)) {
      deleteTargetMutation.mutate(targetId);
    }
  };

  const handleUpdateTargetStatus = (targetId: number, newStatus: 'ACTIVE' | 'INACTIVE') => {
    updateTargetMutation.mutate({
      id: targetId,
      data: { status: newStatus }
    });
  };

  const copyToClipboard = (text: string, label: string) => {
    navigator.clipboard.writeText(text).then(() => {
      toast.success(`${label} copied to clipboard`);
    }).catch(() => {
      toast.error('Failed to copy to clipboard');
    });
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'ACTIVE':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'INACTIVE':
        return <XCircle className="w-4 h-4 text-gray-500" />;
      case 'ERROR':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      case 'PENDING':
        return <Loader2 className="w-4 h-4 text-yellow-500 animate-spin" />;
      default:
        return <AlertCircle className="w-4 h-4 text-gray-500" />;
    }
  };

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const formatFileSize = (bytes: number) => {
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    if (bytes === 0) return '0 B';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${sizes[i]}`;
  };

  if (targetsLoading || machinesLoading || imagesLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
        <span className="ml-2 text-gray-600">Loading target data...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">iSCSI Targets</h2>
          <p className="text-gray-600">Manage iSCSI targets for diskless boot sessions</p>
        </div>
        <div className="flex space-x-3">
          <Button
            onClick={() => refetchTargets()}
            variant="outline"
            className="flex items-center space-x-2"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Refresh</span>
          </Button>
          <Button
            onClick={() => setShowCreateForm(!showCreateForm)}
            className="flex items-center space-x-2"
          >
            <Plus className="w-4 h-4" />
            <span>Create Target</span>
          </Button>
        </div>
      </div>

      {/* Create Target Form */}
      {showCreateForm && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Create New iSCSI Target</h3>
          
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
                      {image.name} ({image.format}) - {formatFileSize(image.size_bytes)}
                    </option>
                  ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            {/* Description */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Description (Optional)
              </label>
              <input
                type="text"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Target description..."
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* LUN ID */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                LUN ID
              </label>
              <input
                type="number"
                value={lunId}
                onChange={(e) => setLunId(parseInt(e.target.value) || 0)}
                min="0"
                max="255"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Initiator IQN */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Initiator IQN (Optional)
              </label>
              <input
                type="text"
                value={initiatorIqn}
                onChange={(e) => setInitiatorIqn(e.target.value)}
                placeholder="Auto-generated if empty"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          <div className="flex justify-end space-x-3">
            <Button
              onClick={() => {
                setShowCreateForm(false);
                resetForm();
              }}
              variant="outline"
            >
              Cancel
            </Button>
            <Button
              onClick={handleCreateTarget}
              disabled={!selectedMachine || !selectedImage || isCreating}
              className="flex items-center space-x-2"
            >
              {isCreating ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Plus className="w-4 h-4" />
              )}
              <span>{isCreating ? 'Creating...' : 'Create Target'}</span>
            </Button>
          </div>
        </Card>
      )}

      {/* Targets List */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">iSCSI Targets</h3>

        {targets.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <HardDrive className="w-12 h-12 mx-auto mb-4 text-gray-300" />
            <p>No iSCSI targets found</p>
            <p className="text-sm">Create your first target to get started</p>
          </div>
        ) : (
          <div className="space-y-4">
            {targets.map((target: any) => {
              const machine = machines.find((m: any) => m.id === target.machine_id);
              const image = images.find((i: any) => i.id === target.image_id);
              
              return (
                <div key={target.id} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-2">
                        <HardDrive className="w-5 h-5 text-blue-500" />
                        <div>
                          <h4 className="text-lg font-medium text-gray-900">
                            {target.target_id}
                          </h4>
                          <p className="text-sm text-gray-500">{target.iqn}</p>
                        </div>
                        <div className="flex items-center">
                          {getStatusIcon(target.status)}
                          <StatusBadge status={target.status} text={target.status} className="ml-2" />
                        </div>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-3">
                        <div>
                          <p className="text-sm font-medium text-gray-700">Machine</p>
                          <p className="text-sm text-gray-900">
                            {machine?.name || 'Unknown'} ({machine?.mac_address || 'N/A'})
                          </p>
                        </div>
                        <div>
                          <p className="text-sm font-medium text-gray-700">Image</p>
                          <p className="text-sm text-gray-900">
                            {image?.name || 'Unknown'} ({image?.format || 'N/A'})
                          </p>
                        </div>
                        <div>
                          <p className="text-sm font-medium text-gray-700">LUN ID</p>
                          <p className="text-sm text-gray-900">{target.lun_id}</p>
                        </div>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-3">
                        <div>
                          <p className="text-sm font-medium text-gray-700">Initiator IQN</p>
                          <div className="flex items-center space-x-2">
                            <p className="text-sm text-gray-900 font-mono">{target.initiator_iqn}</p>
                            <Button
                              onClick={() => copyToClipboard(target.initiator_iqn, 'Initiator IQN')}
                              variant="outline"
                              size="sm"
                              className="p-1"
                            >
                              <Copy className="w-3 h-3" />
                            </Button>
                          </div>
                        </div>
                        <div>
                          <p className="text-sm font-medium text-gray-700">Image Path</p>
                          <div className="flex items-center space-x-2">
                            <p className="text-sm text-gray-900 font-mono truncate">{target.image_path}</p>
                            <Button
                              onClick={() => copyToClipboard(target.image_path, 'Image Path')}
                              variant="outline"
                              size="sm"
                              className="p-1"
                            >
                              <Copy className="w-3 h-3" />
                            </Button>
                          </div>
                        </div>
                      </div>

                      {target.description && (
                        <div className="mb-3">
                          <p className="text-sm font-medium text-gray-700">Description</p>
                          <p className="text-sm text-gray-900">{target.description}</p>
                        </div>
                      )}

                      <div className="flex items-center space-x-4 text-xs text-gray-500">
                        <span>Created: {formatDateTime(target.created_at)}</span>
                        <span>Updated: {formatDateTime(target.updated_at)}</span>
                      </div>
                    </div>

                    <div className="flex flex-col space-y-2 ml-4">
                      {target.status === 'ACTIVE' ? (
                        <Button
                          onClick={() => handleUpdateTargetStatus(target.id, 'INACTIVE')}
                          variant="outline"
                          size="sm"
                          className="text-yellow-600 hover:text-yellow-700"
                        >
                          <Settings className="w-4 h-4 mr-1" />
                          Deactivate
                        </Button>
                      ) : (
                        <Button
                          onClick={() => handleUpdateTargetStatus(target.id, 'ACTIVE')}
                          variant="outline"
                          size="sm"
                          className="text-green-600 hover:text-green-700"
                        >
                          <CheckCircle className="w-4 h-4 mr-1" />
                          Activate
                        </Button>
                      )}
                      
                      <Button
                        onClick={() => handleDeleteTarget(target.id, target.iqn)}
                        variant="outline"
                        size="sm"
                        className="text-red-600 hover:text-red-700"
                      >
                        <Trash2 className="w-4 h-4 mr-1" />
                        Delete
                      </Button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </Card>
    </div>
  );
};

export default TargetManager;
