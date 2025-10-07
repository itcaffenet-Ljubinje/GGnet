import axios, { AxiosInstance } from "axios";
import { useAuthStore } from '../stores/authStore';
import toast from 'react-hot-toast';

// Create an AxiosInstance
export const api: AxiosInstance = axios.create({
  baseURL: "/api",
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
    api.post('/auth/login', { username, password }),
  
  logout: () =>
    api.post('/auth/logout'),
  
  refreshToken: (refreshToken: string) =>
    api.post('/auth/refresh', { refresh_token: refreshToken }),
  
  getCurrentUser: () =>
    api.get('/auth/me'),
  
  changePassword: (currentPassword: string, newPassword: string) =>
    api.post('/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    }),

  // Images
  getImages: (params?: any) =>
    api.get('/images', { params }).then(response => response.data),
  
  getImage: (id: number) =>
    api.get(`/images/${id}`).then(response => response.data),
  
  uploadImage: (formData: FormData, options?: { onProgress?: (progress: number) => void; signal?: AbortSignal }) =>
    api.post('/images/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      signal: options?.signal,
      onUploadProgress: (progressEvent: any) => {
        if (options?.onProgress && progressEvent.total) {
          const progress = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          )
          options.onProgress(progress)
        }
      },
    }).then(response => response.data),
  
  updateImage: (id: number, data: any) =>
    api.put(`/images/${id}`, data).then(response => response.data),
  
  deleteImage: (id: number) =>
    api.delete(`/images/${id}`).then(response => response.data),

  // Machines
  getMachines: (params?: any) =>
    api.get('/machines', { params }).then(response => response.data),
  
  getMachine: (id: number) =>
    api.get(`/machines/${id}`).then(response => response.data),
  
  createMachine: (data: any) =>
    api.post('/machines', data).then(response => response.data),
  
  updateMachine: (id: number, data: any) =>
    api.put(`/machines/${id}`, data).then(response => response.data),
  
  deleteMachine: (id: number) =>
    api.delete(`/machines/${id}`).then(response => response.data),

  // Targets
  getTargets: (params?: any) =>
    api.get('/targets', { params }).then(response => response.data),
  
  getTarget: (id: number) =>
    api.get(`/targets/${id}`).then(response => response.data),
  
  createTarget: (data: any) =>
    api.post('/targets', data).then(response => response.data),
  
  updateTarget: (id: number, data: any) =>
    api.put(`/targets/${id}`, data).then(response => response.data),
  
  deleteTarget: (id: number) =>
    api.delete(`/targets/${id}`).then(response => response.data),

  // Sessions
  getSessions: (params?: any) =>
    api.get('/sessions', { params }).then(response => response.data),
  
  getSessionStatus: (sessionId: string) =>
    api.get(`/sessions/${sessionId}/status`).then(response => response.data),
  
  startSession: (data: any) =>
    api.post('/sessions/start', data).then(response => response.data),
  
  stopSession: (sessionId: string) =>
    api.post(`/sessions/${sessionId}/stop`).then(response => response.data),

  // Storage
  getStorageInfo: () =>
    api.get('/storage/info').then(response => response.data),
  
  getStorageHealth: () =>
    api.get('/storage/health').then(response => response.data),
  
  cleanupStorage: () =>
    api.post('/storage/cleanup').then(response => response.data),

  // Health
  getHealth: () =>
    api.get('/health').then(response => response.data),
  
  getDetailedHealth: () =>
    api.get('/health/detailed').then(response => response.data),

  // Monitoring
  getPerformanceMetrics: () =>
    api.get('/monitoring/metrics').then(response => response.data),
  
  getActiveSessions: () =>
    api.get('/monitoring/sessions/active').then(response => response.data),

  // Session Monitoring
  getSessionStats: () =>
    api.get('/sessions/stats/overview').then(response => response.data),

  getActiveSessionsDetailed: () =>
    api.get('/sessions/active').then(response => response.data),

  getRealtimeSessionData: () =>
    api.get('/sessions/monitoring/realtime').then(response => response.data),

  killSession: (sessionId: string) =>
    api.post(`/sessions/${sessionId}/kill`).then(response => response.data),

  // iSCSI Target Management
  createIscsiTarget: (data: any) =>
    api.post('/iscsi', data).then(response => response.data),

  getIscsiTargets: () =>
    api.get('/iscsi').then(response => response.data),

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