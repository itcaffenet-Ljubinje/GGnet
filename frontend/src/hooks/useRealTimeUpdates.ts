import { useCallback, useMemo } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useWebSocket } from './useWebSocket'
import toast from 'react-hot-toast'

interface RealTimeUpdate {
  type: 'image_uploaded' | 'image_processed' | 'session_started' | 'session_ended' | 'machine_connected' | 'machine_disconnected'
  data: any
  timestamp: string
}

export const useRealTimeUpdates = () => {
  const queryClient = useQueryClient()

  const handleMessage = useCallback((message: RealTimeUpdate) => {
    console.log('Real-time update received:', message)

    // Invalidate relevant queries based on update type
    switch (message.type) {
      case 'image_uploaded':
      case 'image_processed':
        queryClient.invalidateQueries({ queryKey: ['images'] })
        queryClient.invalidateQueries({ queryKey: ['storage'] })
        toast.success(`Image ${message.data.name} ${message.type === 'image_uploaded' ? 'uploaded' : 'processed'} successfully`)
        break

      case 'session_started':
      case 'session_ended':
        queryClient.invalidateQueries({ queryKey: ['sessions'] })
        queryClient.invalidateQueries({ queryKey: ['machines'] })
        toast.success(`Session ${message.type === 'session_started' ? 'started' : 'ended'} for machine ${message.data.machine_name}`)
        break

      case 'machine_connected':
      case 'machine_disconnected':
        queryClient.invalidateQueries({ queryKey: ['machines'] })
        queryClient.invalidateQueries({ queryKey: ['health', 'detailed'] })
        toast.success(`Machine ${message.data.name} ${message.type === 'machine_connected' ? 'connected' : 'disconnected'}`)
        break

      default:
        // Generic update - invalidate all queries
        queryClient.invalidateQueries()
        break
    }
  }, [queryClient])

  // Memoize WebSocket URL to prevent recreating connection on every render
  const wsUrl = useMemo(() => {
    try {
      const authData = localStorage.getItem('auth-storage')
      if (authData) {
        const parsed = JSON.parse(authData)
        const token = parsed.state?.accessToken
        if (token) {
          // Use proxy in development, direct connection in production
          const baseUrl = (import.meta as any).env?.DEV ? 'ws://localhost:3000/ws' : 'ws://localhost:8000/ws'
          return `${baseUrl}?token=${encodeURIComponent(token)}`
        }
      }
    } catch (e) {
      // Ignore parsing errors
    }
    // Use proxy in development, direct connection in production
    const baseUrl = (import.meta as any).env?.DEV ? 'ws://localhost:3000/ws' : 'ws://localhost:8000/ws'
    return baseUrl
  }, [])

  const { isConnected, isConnecting, error, sendMessage } = useWebSocket({
    url: wsUrl,
    onMessage: handleMessage,
    onError: (error) => {
      console.error('WebSocket connection error:', error)
      // Remove toast notification to prevent spam
    },
    onOpen: () => {
      console.log('Real-time updates connected')
      // Remove toast notification to prevent spam
    },
    onClose: () => {
      console.log('Real-time updates disconnected')
      // Remove toast notification to prevent spam
    }
  })

  const sendUpdate = useCallback((type: string, data: any) => {
    const message = {
      type,
      data,
      timestamp: new Date().toISOString()
    }
    sendMessage(message)
  }, [sendMessage])

  return {
    isConnected,
    isConnecting,
    error,
    sendUpdate
  }
}
