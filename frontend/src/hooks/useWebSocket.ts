import { useEffect, useRef, useState, useCallback } from 'react'

interface WebSocketOptions {
  url: string | null
  reconnectInterval?: number
  maxReconnectAttempts?: number
  onOpen?: () => void
  onClose?: () => void
  onError?: (error: Event) => void
  onMessage?: (data: Record<string, unknown>) => void
}

interface WebSocketState {
  isConnected: boolean
  isConnecting: boolean
  error: string | null
  reconnectAttempts: number
}

export const useWebSocket = (options: WebSocketOptions) => {
  const {
    url,
    reconnectInterval = 3000,
    maxReconnectAttempts = 5,
    onOpen,
    onClose,
    onError,
    onMessage
  } = options

  const [state, setState] = useState<WebSocketState>({
    isConnected: false,
    isConnecting: false,
    error: null,
    reconnectAttempts: 0
  })

  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const reconnectAttemptsRef = useRef(0)
  
  // Use refs for callbacks to prevent re-render loops
  const onOpenRef = useRef(onOpen)
  const onCloseRef = useRef(onClose)
  const onErrorRef = useRef(onError)
  const onMessageRef = useRef(onMessage)
  
  // Update refs when callbacks change
  useEffect(() => {
    onOpenRef.current = onOpen
    onCloseRef.current = onClose
    onErrorRef.current = onError
    onMessageRef.current = onMessage
  }, [onOpen, onClose, onError, onMessage])

  const connect = useCallback(() => {
    // Don't connect if URL is null or empty
    if (!url) {
      console.log('WebSocket: No URL provided, skipping connection')
      return
    }
    
    if (wsRef.current?.readyState === WebSocket.OPEN || wsRef.current?.readyState === WebSocket.CONNECTING) {
      return
    }

    setState(prev => ({ ...prev, isConnecting: true, error: null }))

    try {
      console.log('Creating WebSocket connection to:', url)
      wsRef.current = new WebSocket(url)

      wsRef.current.onopen = () => {
        console.log('WebSocket connected successfully')
        setState({
          isConnected: true,
          isConnecting: false,
          error: null,
          reconnectAttempts: 0
        })
        reconnectAttemptsRef.current = 0
        onOpenRef.current?.()
      }

      wsRef.current.onclose = (event) => {
        console.log('WebSocket disconnected', { code: event.code, reason: event.reason, wasClean: event.wasClean })
        setState(prev => ({ ...prev, isConnected: false, isConnecting: false }))
        onCloseRef.current?.()

        // Only attempt to reconnect if it wasn't a manual disconnect (code 1000)
        if (event.code !== 1000 && reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current++
          setState(prev => ({ ...prev, reconnectAttempts: reconnectAttemptsRef.current }))
          
          console.log(`Attempting to reconnect (${reconnectAttemptsRef.current}/${maxReconnectAttempts}) in ${reconnectInterval}ms`)
          reconnectTimeoutRef.current = setTimeout(() => {
            connect()
          }, reconnectInterval)
        } else if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
          console.log('Max reconnection attempts reached')
        }
      }

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error)
        setState(prev => ({ ...prev, error: 'Connection error', isConnecting: false }))
        onErrorRef.current?.(error)
      }

      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          onMessageRef.current?.(data)
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error)
      setState(prev => ({ 
        ...prev, 
        error: 'Failed to connect', 
        isConnecting: false 
      }))
    }
  }, [url, reconnectInterval, maxReconnectAttempts]) // Removed callback deps - using refs instead

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }

    if (wsRef.current) {
      wsRef.current.close(1000, 'Manual disconnect')
      wsRef.current = null
    }

    setState({
      isConnected: false,
      isConnecting: false,
      error: null,
      reconnectAttempts: 0
    })
    reconnectAttemptsRef.current = 0
  }, [])

  const sendMessage = useCallback((message: Record<string, unknown>) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message))
      return true
    }
    return false
  }, [])

  useEffect(() => {
    connect()

    return () => {
      disconnect()
    }
  }, [connect, disconnect]) // Include connect and disconnect dependencies

  return {
    ...state,
    connect,
    disconnect,
    sendMessage
  }
}
