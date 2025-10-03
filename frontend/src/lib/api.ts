// @ts-ignore - Temporary fix until dependencies are installed
import axios, { AxiosInstance } from "axios";

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
  (config: any) => {
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
  (response: any) => {
    return response
  },
  async (error: any) => {
    const originalRequest = error.config

    // Handle 401 errors (unauthorized)
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        // Try to refresh token
        const { useAuthStore } = await import('../stores/authStore')
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
        const { useAuthStore } = await import('../stores/authStore')
        useAuthStore.getState().clearAuth()
        window.location.href = '/login'
      }
    }

    // Handle other errors
    let toast: any = undefined;
    try {
      // @ts-ignore
      const toastModule = await import('react-hot-toast');
      toast = toastModule?.default;
    } catch {
      // If toast cannot be loaded, silently fail
    }

    if (toast) {
      if (error.response?.status >= 500) {
        toast.error('Server error. Please try again later.')
      } else if (error.response?.status === 429) {
        toast.error('Too many requests. Please slow down.')
      }
      // Handle request timeout
      else if (error.code === 'ECONNABORTED' && toast) {
        toast.error('Request timeout. Please check your connection.')
      }
      // Handle network errors (no response)
      else if (!error.response && toast) {
        toast.error('Network error. Please check your connection.')
      }
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
    api.get('/images', { params }),
  
  getImage: (id: number) =>
    api.get(`/images/${id}`),
  
  uploadImage: (formData: FormData, onProgress?: (progress: number) => void) =>
    api.post('/images/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent: any) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          )
          onProgress(progress)
        }
      },
    }),
  
  updateImage: (id: number, data: any) =>
    api.put(`/images/${id}`, data),
  
  deleteImage: (id: number) =>
    api.delete(`/images/${id}`),

  // Machines
  getMachines: (params?: any) =>
    api.get('/machines', { params }),
  
  getMachine: (id: number) =>
    api.get(`/machines/${id}`),
  
  createMachine: (data: any) =>
    api.post('/machines', data),
  
  updateMachine: (id: number, data: any) =>
    api.put(`/machines/${id}`, data),
  
  deleteMachine: (id: number) =>
    api.delete(`/machines/${id}`),

  // Targets
  getTargets: (params?: any) =>
    api.get('/targets', { params }),
  
  getTarget: (id: number) =>
    api.get(`/targets/${id}`),
  
  createTarget: (data: any) =>
    api.post('/targets', data),
  
  updateTarget: (id: number, data: any) =>
    api.put(`/targets/${id}`, data),
  
  deleteTarget: (id: number) =>
    api.delete(`/targets/${id}`),

  // Sessions
  getSessions: (params?: any) =>
    api.get('/sessions', { params }),
  
  getSessionStatus: (sessionId: string) =>
    api.get(`/sessions/${sessionId}/status`),
  
  startSession: (data: any) =>
    api.post('/sessions/start', data),
  
  stopSession: (sessionId: string) =>
    api.post(`/sessions/${sessionId}/stop`),

  // Storage
  getStorageInfo: () =>
    api.get('/storage/info'),
  
  getStorageHealth: () =>
    api.get('/storage/health'),
  
  cleanupStorage: () =>
    api.post('/storage/cleanup'),

  // Health
  getHealth: () =>
    api.get('/health'),
  
  getDetailedHealth: () =>
    api.get('/health/detailed'),
}

export default api