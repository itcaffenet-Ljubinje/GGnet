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

interface ImageData {
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
  baseURL: "",  // No prefix - paths should include /api if needed
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
  
  updateImage: (id: number, data: ImageData) =>
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
  
  getStorageHealth: () =>
    api.get('/api/storage/health').then(response => response.data),
  
  cleanupStorage: () =>
    api.post('/api/storage/cleanup').then(response => response.data),

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
  
}

export default api
