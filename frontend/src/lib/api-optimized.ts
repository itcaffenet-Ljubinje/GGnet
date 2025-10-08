import axios, { AxiosInstance, AxiosProgressEvent, AxiosRequestConfig } from "axios";
import { useAuthStore } from '../stores/authStore';
import toast from 'react-hot-toast';

// Cache configuration
const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes
const requestCache = new Map<string, { data: any; timestamp: number }>();
const pendingRequests = new Map<string, Promise<any>>();

// Create cache key from request config
function getCacheKey(config: AxiosRequestConfig): string {
  const params = config.params ? JSON.stringify(config.params) : '';
  return `${config.method}:${config.url}:${params}`;
}

// Check if cache is valid
function isCacheValid(timestamp: number): boolean {
  return Date.now() - timestamp < CACHE_DURATION;
}

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

// Create an optimized AxiosInstance
export const api: AxiosInstance = axios.create({
  baseURL: "",
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor with caching and deduplication
api.interceptors.request.use(
  async (config) => {
    // Add authentication token
    const token = localStorage.getItem('auth-storage');
    if (token) {
      try {
        const authData = JSON.parse(token);
        if (authData.state?.accessToken) {
          config.headers.Authorization = `Bearer ${authData.state.accessToken}`;
        }
      } catch (e) {
        // Ignore parsing errors
      }
    }
    
    // Check cache for GET requests
    if (config.method === 'get') {
      const cacheKey = getCacheKey(config);
      
      // Check if request is already pending (deduplication)
      const pendingRequest = pendingRequests.get(cacheKey);
      if (pendingRequest) {
        return Promise.reject({
          __cached: true,
          __pending: true,
          promise: pendingRequest
        });
      }
      
      // Check cache
      const cached = requestCache.get(cacheKey);
      if (cached && isCacheValid(cached.timestamp)) {
        return Promise.reject({
          __cached: true,
          data: cached.data
        });
      }
    }
    
    return config;
  },
  (error: unknown) => {
    return Promise.reject(error);
  }
);

// Response interceptor with caching
api.interceptors.response.use(
  (response) => {
    // Cache successful GET responses
    if (response.config.method === 'get') {
      const cacheKey = getCacheKey(response.config);
      requestCache.set(cacheKey, {
        data: response.data,
        timestamp: Date.now()
      });
      
      // Remove from pending requests
      pendingRequests.delete(cacheKey);
    }
    
    return response;
  },
  async (error) => {
    // Handle cached responses
    if (error.__cached) {
      if (error.__pending) {
        // Wait for pending request
        return error.promise;
      }
      // Return cached data
      return { data: error.data };
    }
    
    const originalRequest = error.config;

    // Handle 401 errors (unauthorized)
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const success = await useAuthStore.getState().refreshAuth();
        
        if (success) {
          return api(originalRequest);
        } else {
          useAuthStore.getState().clearAuth();
          window.location.href = '/login';
        }
      } catch (refreshError) {
        useAuthStore.getState().clearAuth();
        window.location.href = '/login';
      }
    }

    // Handle other errors
    if (error.response?.status >= 500) {
      toast.error('Server error. Please try again later.');
    } else if (error.response?.status === 429) {
      toast.error('Too many requests. Please slow down.');
    } else if (error.code === 'ECONNABORTED') {
      toast.error('Request timeout. Please check your connection.');
    } else if (!error.response) {
      toast.error('Network error. Please check your connection.');
    }

    return Promise.reject(error);
  }
);

// Optimized API helper with request deduplication
function createOptimizedRequest<T>(
  method: 'get' | 'post' | 'put' | 'delete',
  url: string,
  data?: any,
  config?: AxiosRequestConfig
): Promise<T> {
  const requestConfig = { ...config, method, url, data };
  
  if (method === 'get') {
    const cacheKey = getCacheKey(requestConfig);
    
    // Check if request is already pending
    const pending = pendingRequests.get(cacheKey);
    if (pending) {
      return pending;
    }
    
    // Create new request and store as pending
    const request = api.request<T>(requestConfig).then(response => response.data);
    pendingRequests.set(cacheKey, request);
    
    // Clean up pending request after completion
    request.finally(() => {
      pendingRequests.delete(cacheKey);
    });
    
    return request;
  }
  
  // Non-GET requests bypass caching
  return api.request<T>(requestConfig).then(response => response.data);
}

// Cache management utilities
export const cacheUtils = {
  clearCache: () => {
    requestCache.clear();
    pendingRequests.clear();
  },
  
  clearCacheForPattern: (pattern: string) => {
    for (const key of requestCache.keys()) {
      if (key.includes(pattern)) {
        requestCache.delete(key);
      }
    }
  },
  
  getCacheSize: () => requestCache.size,
  
  getCacheStats: () => ({
    size: requestCache.size,
    pendingRequests: pendingRequests.size,
    entries: Array.from(requestCache.keys())
  })
};

// Optimized API helper functions with automatic caching
export const apiHelpers = {
  // Auth
  login: (username: string, password: string) =>
    createOptimizedRequest<any>('post', '/api/auth/login', { username, password }),
  
  logout: () =>
    createOptimizedRequest<any>('post', '/api/auth/logout').then(() => {
      cacheUtils.clearCache(); // Clear all cache on logout
    }),
  
  refreshToken: (refreshToken: string) =>
    createOptimizedRequest<any>('post', '/api/auth/refresh', { refresh_token: refreshToken }),
  
  getCurrentUser: () =>
    createOptimizedRequest<any>('get', '/api/auth/me'),
  
  changePassword: (currentPassword: string, newPassword: string) =>
    createOptimizedRequest<any>('post', '/api/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    }),

  // Images - with cache invalidation on mutations
  getImages: (params?: QueryParams) =>
    createOptimizedRequest<any>('get', '/api/images', undefined, { params }),
  
  getImage: (id: number) =>
    createOptimizedRequest<any>('get', `/api/images/${id}`),
  
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
          );
          options.onProgress(progress);
        }
      },
    }).then(response => {
      cacheUtils.clearCacheForPattern('/api/images');
      return response.data;
    }),
  
  updateImage: (id: number, data: ImageData) =>
    createOptimizedRequest<any>('put', `/api/images/${id}`, data).then(result => {
      cacheUtils.clearCacheForPattern('/api/images');
      return result;
    }),
  
  deleteImage: (id: number) =>
    createOptimizedRequest<any>('delete', `/api/images/${id}`).then(result => {
      cacheUtils.clearCacheForPattern('/api/images');
      return result;
    }),

  // Machines - with cache invalidation
  getMachines: (params?: QueryParams) =>
    createOptimizedRequest<any>('get', '/api/machines', undefined, { params }),
  
  getMachine: (id: number) =>
    createOptimizedRequest<any>('get', `/api/machines/${id}`),
  
  createMachine: (data: MachineData) =>
    createOptimizedRequest<any>('post', '/api/machines', data).then(result => {
      cacheUtils.clearCacheForPattern('/api/machines');
      return result;
    }),
  
  updateMachine: (id: number, data: Partial<MachineData>) =>
    createOptimizedRequest<any>('put', `/api/machines/${id}`, data).then(result => {
      cacheUtils.clearCacheForPattern('/api/machines');
      return result;
    }),
  
  deleteMachine: (id: number) =>
    createOptimizedRequest<any>('delete', `/api/machines/${id}`).then(result => {
      cacheUtils.clearCacheForPattern('/api/machines');
      return result;
    }),

  // Targets
  getTargets: (params?: QueryParams) =>
    createOptimizedRequest<any>('get', '/api/api/v1/targets', undefined, { params }),
  
  getTarget: (id: number) =>
    createOptimizedRequest<any>('get', `/api/api/v1/targets/${id}`),
  
  createTarget: (data: TargetData) =>
    createOptimizedRequest<any>('post', '/api/api/v1/targets', data).then(result => {
      cacheUtils.clearCacheForPattern('/api/api/v1/targets');
      return result;
    }),
  
  updateTarget: (id: number, data: Partial<TargetData>) =>
    createOptimizedRequest<any>('put', `/api/api/v1/targets/${id}`, data).then(result => {
      cacheUtils.clearCacheForPattern('/api/api/v1/targets');
      return result;
    }),
  
  deleteTarget: (id: number) =>
    createOptimizedRequest<any>('delete', `/api/api/v1/targets/${id}`).then(result => {
      cacheUtils.clearCacheForPattern('/api/api/v1/targets');
      return result;
    }),

  // Sessions - no caching for real-time data
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
    createOptimizedRequest<any>('get', '/api/storage/info'),
  
  getStorageHealth: () =>
    createOptimizedRequest<any>('get', '/api/storage/health'),
  
  cleanupStorage: () =>
    createOptimizedRequest<any>('post', '/api/storage/cleanup').then(result => {
      cacheUtils.clearCacheForPattern('/api/storage');
      return result;
    }),

  // Health - short cache for health checks
  getHealth: () =>
    api.get('/api/health').then(response => response.data), // No cache for health
  
  getDetailedHealth: () =>
    createOptimizedRequest<any>('get', '/api/health/detailed'),

  // Monitoring - no cache for real-time metrics
  getPerformanceMetrics: () =>
    api.get('/api/monitoring/metrics').then(response => response.data),
  
  getActiveSessions: () =>
    api.get('/api/monitoring/sessions/active').then(response => response.data),

  // Session Monitoring - no cache for real-time data
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
    createOptimizedRequest<any>('post', '/api/iscsi', data).then(result => {
      cacheUtils.clearCacheForPattern('/api/iscsi');
      return result;
    }),

  getIscsiTargets: () =>
    createOptimizedRequest<any>('get', '/api/iscsi'),

  getIscsiTarget: (id: number) =>
    createOptimizedRequest<any>('get', `/iscsi/${id}`),

  deleteIscsiTarget: (id: number) =>
    createOptimizedRequest<any>('delete', `/iscsi/${id}`).then(result => {
      cacheUtils.clearCacheForPattern('/iscsi');
      return result;
    }),

  startIscsiTarget: (id: number) =>
    createOptimizedRequest<any>('post', `/iscsi/${id}/start`).then(result => {
      cacheUtils.clearCacheForPattern(`/iscsi/${id}`);
      return result;
    }),

  stopIscsiTarget: (id: number) =>
    createOptimizedRequest<any>('post', `/iscsi/${id}/stop`).then(result => {
      cacheUtils.clearCacheForPattern(`/iscsi/${id}`);
      return result;
    }),
};

export default api;