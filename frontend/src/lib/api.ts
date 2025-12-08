import axios, { AxiosInstance, AxiosProgressEvent } from "axios";
import { useAuthStore } from '../stores/authStore';
import toast from 'react-hot-toast';

// API parameter types
interface QueryParams {
  page?: number;
  limit?: number;
  search?: string;
  sort?: string;
  [key: string]: string | number | boolean | undefined;
}

interface ImageUploadData {
  name?: string;
  description?: string;
  format?: string;
  [key: string]: unknown;
}

interface MachineData {
  name: string;
  hostname: string;
  ip_address: string;
  mac_address: string;
  asset_tag?: string;
  description?: string;
  [key: string]: unknown;
}

interface TargetData {
  machine_id: number;
  image_id: number;
  [key: string]: unknown;
}

interface SessionData {
  machine_id: number;
  image_id: number;
  [key: string]: unknown;
}

// Create an AxiosInstance
export const api: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "",  // Use VITE_API_URL from environment, fallback to empty for relative URLs
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});
  
// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add authentication token
    const token = localStorage.getItem('auth-storage')
    if (token) {
      try {
        const authData = JSON.parse(token)
        if (authData.state?.accessToken) {
          config.headers.Authorization = `Bearer ${authData.state.accessToken}`
        }
      } catch (e) {
        // Ignore parsing errors
      }
    }
    
    // Add timestamp to prevent caching
    if (config.method === 'get') {
      config.params = {
        ...config.params,
        _t: Date.now(),
      }
    }
    
    return config
  },
  (error: unknown) => {
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response
  },
  async (error) => {
    const originalRequest = error.config

    // Handle 401 errors (unauthorized)
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        // Try to refresh token
        const success = await useAuthStore.getState().refreshAuth()
        
        if (success) {
          // Retry original request
          return api(originalRequest)
        } else {
          // Refresh failed, redirect to login
          useAuthStore.getState().clearAuth()
          window.location.href = '/login'
        }
      } catch (refreshError) {
        // Refresh failed, redirect to login
        useAuthStore.getState().clearAuth()
        window.location.href = '/login'
      }
    }

    // Handle other errors
    if (error.response?.status >= 500) {
      toast.error('Server error. Please try again later.')
    } else if (error.response?.status === 429) {
      toast.error('Too many requests. Please slow down.')
    } else if (error.code === 'ECONNABORTED') {
      toast.error('Request timeout. Please check your connection.')
    } else if (!error.response) {
      toast.error('Network error. Please check your connection.')
    }

    return Promise.reject(error)
  }
)

// API helper functions
export const apiHelpers = {
  // Auth
  login: (username: string, password: string) =>
    api.post('/api/auth/login', { username, password }),
  
  logout: () =>
    api.post('/api/auth/logout'),
  
  refreshToken: (refreshToken: string) =>
    api.post('/api/auth/refresh', { refresh_token: refreshToken }),
  
  getCurrentUser: () =>
    api.get('/api/auth/me'),
  
  changePassword: (currentPassword: string, newPassword: string) =>
    api.post('/api/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    }),

  // Images
  getImages: (params?: QueryParams) =>
    api.get('/api/images', { params }).then(response => response.data),
  
  getImage: (id: number) =>
    api.get(`/api/images/${id}`).then(response => response.data),
  
  uploadImage: (formData: FormData, options?: { onProgress?: (progress: number) => void; signal?: AbortSignal }) =>
    api.post('/api/images/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      signal: options?.signal,
      onUploadProgress: (progressEvent: AxiosProgressEvent) => {
        if (options?.onProgress && progressEvent.total) {
          const progress = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          )
          options.onProgress(progress)
        }
      },
    }).then(response => response.data),
  
  updateImage: (id: number, data: ImageUploadData) =>
    api.put(`/api/images/${id}`, data).then(response => response.data),
  
  deleteImage: (id: number) =>
    api.delete(`/api/images/${id}`).then(response => response.data),

  // Machines
  getMachines: (params?: QueryParams) =>
    api.get('/api/machines', { params }).then(response => response.data),
  
  getMachine: (id: number) =>
    api.get(`/api/machines/${id}`).then(response => response.data),
  
  createMachine: (data: MachineData) =>
    api.post('/api/machines', data).then(response => response.data),
  
  updateMachine: (id: number, data: Partial<MachineData>) =>
    api.put(`/api/machines/${id}`, data).then(response => response.data),
  
  deleteMachine: (id: number) =>
    api.delete(`/api/machines/${id}`).then(response => response.data),

  // Targets
  getTargets: (params?: QueryParams) =>
    api.get('/api/api/v1/targets', { params }).then(response => response.data),
  
  getTarget: (id: number) =>
    api.get(`/api/api/v1/targets/${id}`).then(response => response.data),
  
  createTarget: (data: TargetData) =>
    api.post('/api/api/v1/targets', data).then(response => response.data),
  
  updateTarget: (id: number, data: Partial<TargetData>) =>
    api.put(`/api/api/v1/targets/${id}`, data).then(response => response.data),
  
  deleteTarget: (id: number) =>
    api.delete(`/api/api/v1/targets/${id}`).then(response => response.data),

  // Sessions
  getSessions: (params?: QueryParams) =>
    api.get('/api/api/v1/sessions', { params }).then(response => response.data),
  
  getSessionStatus: (sessionId: string) =>
    api.get(`/api/api/v1/sessions/${sessionId}/status`).then(response => response.data),
  
  startSession: (data: SessionData) =>
    api.post('/api/api/v1/sessions/start', data).then(response => response.data),
  
  stopSession: (sessionId: string) =>
    api.post(`/api/api/v1/sessions/${sessionId}/stop`).then(response => response.data),

  // Storage
  getStorageInfo: () =>
    api.get('/api/storage/info').then(response => response.data),
  
  getStorageMounts: () =>
    api.get('/api/storage/mounts').then(response => response.data),
  
  getStorageHealth: () =>
    api.get('/api/storage/health').then(response => response.data),
  
  cleanupStorage: () =>
    api.post('/api/storage/cleanup').then(response => response.data),

  // ZFS
  getZfsPools: () =>
    api.get('/api/zfs/pools').then(response => response.data),
  
  getZfsPoolInfo: (poolName: string) =>
    api.get(`/api/zfs/pools/${poolName}`).then(response => response.data),
  
  getZfsDatasets: (poolName?: string) =>
    api.get('/api/zfs/datasets', { params: poolName ? { pool_name: poolName } : {} }).then(response => response.data),
  
  getZfsSnapshots: (datasetName?: string) =>
    api.get('/api/zfs/snapshots', { params: datasetName ? { dataset_name: datasetName } : {} }).then(response => response.data),
  
  createZfsPool: (data: { pool_name: string; vdevs: string[]; pool_type?: string; mountpoint?: string }) =>
    api.post('/api/zfs/pools', data).then(response => response.data),
  
  destroyZfsPool: (poolName: string, force?: boolean) =>
    api.delete(`/api/zfs/pools/${poolName}`, { params: force ? { force: true } : {} }).then(response => response.data),
  
  createZfsDataset: (data: { dataset_name: string; pool_name: string; properties?: Record<string, string> }) =>
    api.post('/api/zfs/datasets', data).then(response => response.data),
  
  createZfsSnapshot: (data: { dataset_name: string; snapshot_name: string }) =>
    api.post('/api/zfs/snapshots', data).then(response => response.data),

  // Health
  getHealth: () =>
    api.get('/api/health').then(response => response.data),
  
  getDetailedHealth: () =>
    api.get('/api/health/detailed').then(response => response.data),

  // Monitoring
  getPerformanceMetrics: () =>
    api.get('/api/monitoring/metrics').then(response => response.data),
  
  getActiveSessions: () =>
    api.get('/api/monitoring/sessions/active').then(response => response.data),

  // Session Monitoring
  getSessionStats: () =>
    api.get('/api/sessions/stats/overview').then(response => response.data),

  getActiveSessionsDetailed: () =>
    api.get('/api/sessions/active').then(response => response.data),

  getRealtimeSessionData: () =>
    api.get('/api/sessions/monitoring/realtime').then(response => response.data),

  killSession: (sessionId: string) =>
    api.post(`/sessions/${sessionId}/kill`).then(response => response.data),

  // iSCSI Target Management
  createIscsiTarget: (data: TargetData) =>
    api.post('/api/iscsi', data).then(response => response.data),

  getIscsiTargets: () =>
    api.get('/api/iscsi').then(response => response.data),

  getIscsiTarget: (id: number) =>
    api.get(`/iscsi/${id}`).then(response => response.data),

  deleteIscsiTarget: (id: number) =>
    api.delete(`/iscsi/${id}`).then(response => response.data),

  startIscsiTarget: (id: number) =>
    api.post(`/iscsi/${id}/start`).then(response => response.data),

  stopIscsiTarget: (id: number) =>
    api.post(`/iscsi/${id}/stop`).then(response => response.data),

  // Writebacks
  getWritebacks: (params?: { machine_id?: number; image_id?: number }) =>
    api.get('/api/v1/writebacks', { params }).then(response => response.data),
  
  getWriteback: (id: number) =>
    api.get(`/api/v1/writebacks/${id}`).then(response => response.data),
  
  keepWriteback: (id: number) =>
    api.post(`/api/v1/writebacks/${id}/keep`).then(response => response.data),
  
  deleteWriteback: (id: number) =>
    api.delete(`/api/v1/writebacks/${id}`).then(response => response.data),

  // Snapshots
  getSnapshots: (params?: { image_id?: number; machine_id?: number; start_date?: string; end_date?: string }) =>
    api.get('/api/v1/snapshots', { params }).then(response => response.data),
  
  getSnapshot: (id: number) =>
    api.get(`/api/v1/snapshots/${id}`).then(response => response.data),
  
  createSnapshot: (data: { image_id: number; machine_id?: number; description?: string }) =>
    api.post('/api/v1/snapshots', data).then(response => response.data),
  
  deleteSnapshot: (id: number) =>
    api.delete(`/api/v1/snapshots/${id}`).then(response => response.data),
  
  applyRetentionPolicy: (data: { image_id?: number; policy: string; days?: number; count?: number }) =>
    api.post('/api/v1/snapshots/apply-retention', data).then(response => response.data),
  
  getSnapshotStats: () =>
    api.get('/api/v1/snapshots/stats').then(response => response.data),

  // Scheduler
  getScheduledJobs: (params?: { status?: string; job_type?: string }) =>
    api.get('/api/v1/scheduler', { params }).then(response => response.data),
  
  getScheduledJob: (id: number) =>
    api.get(`/api/v1/scheduler/${id}`).then(response => response.data),
  
  createScheduledJob: (data: {
    name: string;
    job_type: string;
    schedule_type: string;
    schedule_data: Record<string, unknown>;
    behavior_data: Record<string, unknown>;
    enabled?: boolean;
  }) =>
    api.post('/api/v1/scheduler', data).then(response => response.data),
  
  updateScheduledJob: (id: number, data: Partial<{
    name: string;
    schedule_type: string;
    schedule_data: Record<string, unknown>;
    behavior_data: Record<string, unknown>;
    enabled: boolean;
  }>) =>
    api.put(`/api/v1/scheduler/${id}`, data).then(response => response.data),
  
  deleteScheduledJob: (id: number) =>
    api.delete(`/api/v1/scheduler/${id}`).then(response => response.data),
  
  pauseScheduledJob: (id: number) =>
    api.post(`/api/v1/scheduler/${id}/pause`).then(response => response.data),
  
  resumeScheduledJob: (id: number) =>
    api.post(`/api/v1/scheduler/${id}/resume`).then(response => response.data),
  
  runScheduledJob: (id: number) =>
    api.post(`/api/v1/scheduler/${id}/run-now`).then(response => response.data),
  
  getJobExecutions: (jobId: number, params?: { limit?: number; offset?: number }) =>
    api.get(`/api/v1/scheduler/${jobId}/executions`, { params }).then(response => response.data),
  
  getBehaviors: () =>
    api.get('/api/v1/scheduler/behaviors').then(response => response.data),

  // Activities
  getActivities: (params?: {
    user_id?: number;
    activity_type?: string;
    level?: string;
    start_date?: string;
    end_date?: string;
    limit?: number;
    offset?: number;
  }) =>
    api.get('/api/v1/activities', { params }).then(response => response.data),
  
  getActivityStats: (params?: { start_date?: string; end_date?: string }) =>
    api.get('/api/v1/activities/stats', { params }).then(response => response.data),
  
  getActivityTypes: () =>
    api.get('/api/v1/activities/types').then(response => response.data),

  // Batch Operations
  batchBackupImages: (data: { image_ids: number[]; backup_path: string; is_remote?: boolean; remote_host?: string; remote_path?: string }) =>
    api.post('/api/v1/batch/images/backup', data).then(response => response.data),
  
  batchRestoreImages: (data: { image_ids: number[]; backup_path: string; is_remote?: boolean }) =>
    api.post('/api/v1/batch/images/restore', data).then(response => response.data),
  
  batchTestImages: (data: { image_ids: number[]; backup_path: string }) =>
    api.post('/api/v1/batch/images/test', data).then(response => response.data),
  
  batchOperateMachines: (data: { machine_ids: number[]; operation_type: string }) =>
    api.post('/api/v1/batch/machines', data).then(response => response.data),
  
  getBatchOperation: (id: number) =>
    api.get(`/api/v1/batch/operations/${id}`).then(response => response.data),
  
  cancelBatchOperation: (id: number) =>
    api.post(`/api/v1/batch/operations/${id}/cancel`).then(response => response.data),
  
  listBatchOperations: (params?: { operation_type?: string; status?: string; limit?: number }) =>
    api.get('/api/v1/batch/operations', { params }).then(response => response.data),

  // VMs
  getVMs: (params?: { skip?: number; limit?: number; status?: string }) =>
    api.get('/api/v1/vms', { params }).then(response => response.data),
  
  getVM: (id: number) =>
    api.get(`/api/v1/vms/${id}`).then(response => response.data),
  
  createVM: (data: {
    name: string;
    image_id: number;
    vcpus?: number;
    ram_mb?: number;
    drives_connection?: string;
    mac_address?: string;
    boot_mode?: string;
    description?: string;
  }) =>
    api.post('/api/v1/vms', data).then(response => response.data),
  
  deleteVM: (id: number, force?: boolean) =>
    api.delete(`/api/v1/vms/${id}`, { params: force ? { force: true } : {} }).then(response => response.data),
  
  startVM: (id: number) =>
    api.post(`/api/v1/vms/${id}/start`).then(response => response.data),
  
  stopVM: (id: number, force?: boolean) =>
    api.post(`/api/v1/vms/${id}/stop`, {}, { params: force ? { force: true } : {} }).then(response => response.data),
  
  getVMVNC: (id: number) =>
    api.get(`/api/v1/vms/${id}/vnc`).then(response => response.data),

  // Clients
  getClients: (params?: { skip?: number; limit?: number; status?: string }) =>
    api.get('/api/v1/clients', { params }).then(response => response.data),
  
  getClient: (clientId: string) =>
    api.get(`/api/v1/clients/${clientId}`).then(response => response.data),
  
  registerClient: (data: {
    client_id: string;
    hostname?: string;
    ip_address?: string;
    os_version?: string;
    mac_address?: string;
    metadata?: Record<string, unknown>;
  }) =>
    api.post('/api/v1/clients/register', data).then(response => response.data),
  
  getClientStatus: (clientId: string) =>
    api.get(`/api/v1/clients/${clientId}/status`).then(response => response.data),
  
  sendClientMessage: (clientId: string, message: Record<string, unknown>) =>
    api.post(`/api/v1/clients/${clientId}/message`, { message }).then(response => response.data),
  
  broadcastMessage: (message: Record<string, unknown>, exclude?: string[]) =>
    api.post('/api/v1/clients/broadcast', { message }, { params: exclude ? { exclude } : {} }).then(response => response.data),
  
  getConnectedClients: () =>
    api.get('/api/v1/clients/connected/list').then(response => response.data),

  // Image Import/Export
  importImage: (data: {
    name: string;
    source_path: string;
    image_type?: string;
    description?: string;
  }) =>
    api.post('/api/v1/images/import-export/import', data).then(response => response.data),
  
  importImageUpload: (formData: FormData) =>
    api.post('/api/v1/images/import-export/import/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then(response => response.data),
  
  exportImage: (imageId: number, data: {
    destination_path?: string;
    format?: string;
    compress?: boolean;
  }) =>
    api.post(`/api/v1/images/import-export/${imageId}/export`, data).then(response => response.data),
  
  exportImageForDownload: (imageId: number, data: {
    format?: string;
    compress?: boolean;
  }) =>
    api.post(`/api/v1/images/import-export/${imageId}/export/download`, data).then(response => response.data),
  
  getExportStatus: (imageId: number) =>
    api.get(`/api/v1/images/import-export/${imageId}/export/status`).then(response => response.data),
  
  downloadExportedImage: (imageId: number, filename: string) =>
    api.get(`/api/v1/images/import-export/${imageId}/export/download/${filename}`, {
      responseType: 'blob',
    }),

  // Enhanced ZFS
  getZfsArcStats: () =>
    api.get('/api/zfs/arc/stats').then(response => response.data),
  
  getZfsPoolIostat: (poolName: string) =>
    api.get(`/api/zfs/pools/${poolName}/iostat`).then(response => response.data),
  
  startZfsPoolScrub: (poolName: string) =>
    api.post(`/api/zfs/pools/${poolName}/scrub`).then(response => response.data),
  
  getZfsPoolStatus: (poolName: string) =>
    api.get(`/api/zfs/pools/${poolName}/status`).then(response => response.data),

  // Network Boot
  getBootEvents: (params?: {
    machine_id?: number;
    session_id?: number;
    event_type?: string;
    status?: string;
    start_date?: string;
    end_date?: string;
    limit?: number;
    skip?: number;
  }) =>
    api.get('/api/v1/monitoring/boot-events', { params }).then(response => response.data),
  
  createBootEvent: (data: {
    machine_id?: number;
    session_id?: number;
    event_type: string;
    status: string;
    message: string;
    details?: Record<string, unknown>;
    client_ip?: string;
    server_ip?: string;
    mac_address?: string;
  }) =>
    api.post('/api/v1/monitoring/boot-events', data).then(response => response.data),
  
  getBootStatistics: (params?: {
    machine_id?: number;
    start_date?: string;
    end_date?: string;
  }) =>
    api.get('/api/v1/monitoring/boot-statistics', { params }).then(response => response.data),
  
  getMachineBootStatus: (machineId: number) =>
    api.get(`/api/v1/monitoring/machine-boot-status/${machineId}`).then(response => response.data),
  
  getNetworkServices: () =>
    api.get('/api/v1/monitoring/network-services').then(response => response.data),
  
  getDHCPStatus: () =>
    api.get('/api/v1/network-boot/dhcp/status').then(response => response.data),
  
  getTFTPStatus: () =>
    api.get('/api/v1/network-boot/tftp/status').then(response => response.data),
  
  generateIPXEScript: (machineId: number) =>
    api.get(`/api/v1/network-boot/ipxe/${machineId}`).then(response => response.data),

  // Pre-flight Checks
  runPreflightChecks: () =>
    api.get('/api/preflight').then(response => response.data),
  
  runSinglePreflightCheck: (checkName: string) =>
    api.get(`/api/preflight/${checkName}`).then(response => response.data),

  // Hardware Detection
  detectHardware: (data: {
    machine_id?: number;
    mac_address?: string;
    hardware: {
      cpu_info?: string;
      cpu_cores?: number;
      cpu_threads?: number;
      cpu_frequency_mhz?: number;
      memory_mb?: number;
      memory_total_gb?: number;
      disk_info?: string;
      disk_count?: number;
      disk_total_gb?: number;
      gpu_info?: string;
      gpu_count?: number;
      motherboard?: string;
      bios_version?: string;
      network_adapters?: Array<Record<string, unknown>>;
      usb_devices?: Array<Record<string, unknown>>;
      pci_devices?: Array<Record<string, unknown>>;
    };
  }) =>
    api.post('/api/v1/hardware/detect', data).then(response => response.data),
  
  getMachineHardware: (machineId: number) =>
    api.get(`/api/v1/hardware/machine/${machineId}`).then(response => response.data),
  
  matchMachinesByHardware: (params?: { cpu_info?: string; memory_mb?: number; gpu_info?: string }) =>
    api.get('/api/v1/hardware/match', { params }).then(response => response.data),

  // Windows Registry Scripts
  createRegistryScript: (data: {
    name: string;
    description?: string;
    entries: Array<{
      key: string;
      value_name: string;
      value_type: string;
      value: unknown;
      description?: string;
    }>;
    machine_id?: number;
    image_id?: number;
    apply_on_boot?: boolean;
  }) =>
    api.post('/api/v1/windows-registry', data).then(response => response.data),
  
  listRegistryScripts: (params?: { machine_id?: number; image_id?: number }) =>
    api.get('/api/v1/windows-registry', { params }).then(response => response.data),
  
  getRegistryScript: (scriptId: number, format?: 'reg' | 'ps') =>
    api.get(`/api/v1/windows-registry/${scriptId}`, { params: { format } }).then(response => response.data),
  
  getMachineRegistryScript: (machineId: number, format?: 'reg' | 'ps') =>
    api.get(`/api/v1/windows-registry/machine/${machineId}/script`, { params: { format } }).then(response => response.data),

  // iPXE Binaries
  uploadIPXEBinary: (file: File, description?: string) => {
    const formData = new FormData();
    formData.append('file', file);
    if (description) formData.append('description', description);
    return api.post('/api/v1/ipxe-binaries/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    }).then(response => response.data);
  },
  
  listIPXEBinaries: (params?: { binary_type?: string; architecture?: string; secureboot?: boolean }) =>
    api.get('/api/v1/ipxe-binaries', { params }).then(response => response.data),
  
  getIPXEBinary: (filename: string) =>
    api.get(`/api/v1/ipxe-binaries/${filename}`).then(response => response.data),
  
  deleteIPXEBinary: (filename: string) =>
    api.delete(`/api/v1/ipxe-binaries/${filename}`).then(response => response.data),
  
  getRecommendedIPXEBinary: (bootMode: string, architecture?: string) =>
    api.get(`/api/v1/ipxe-binaries/recommended/${bootMode}`, { params: { architecture } }).then(response => response.data),

  // VNC Console
  createVNCConnection: (data: { machine_id: number; vnc_host?: string; vnc_port?: number; vnc_password?: string }) =>
    api.post('/api/v1/vnc/connect', data).then(response => response.data),
  
  getVNCConnection: (machineId: number) =>
    api.get(`/api/v1/vnc/machine/${machineId}`).then(response => response.data),
  
  listVNCConnections: () =>
    api.get('/api/v1/vnc').then(response => response.data),
  
  disconnectVNC: (machineId: number) =>
    api.delete(`/api/v1/vnc/machine/${machineId}`).then(response => response.data),
  
  getVNCConsoleURL: (connectionId: string) =>
    `/api/v1/vnc/console/${connectionId}`,
}

export default api
