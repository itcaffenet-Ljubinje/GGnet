// Vitest globals are available via globals: true in vitest.config.ts
import { renderHook } from '@testing-library/react'
import { useRealTimeUpdates } from './useRealTimeUpdates'
import { useWebSocket } from './useWebSocket'
import { useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'

// Mock dependencies
vi.mock('./useWebSocket')
vi.mock('@tanstack/react-query')
vi.mock('react-hot-toast', () => ({
  default: {
    success: vi.fn(),
    error: vi.fn(),
  },
}))

describe('useRealTimeUpdates', () => {
  const mockInvalidateQueries = vi.fn()
  const mockQueryClient = {
    invalidateQueries: mockInvalidateQueries,
  }
  const mockSendMessage = vi.fn()
  const mockUseWebSocket = vi.mocked(useWebSocket)

  beforeEach(() => {
    vi.clearAllMocks()
    
    vi.mocked(useQueryClient).mockReturnValue(mockQueryClient as unknown as ReturnType<typeof useQueryClient>)
    
    // Setup localStorage with auth token
    localStorage.setItem('auth-storage', JSON.stringify({
      state: {
        accessToken: 'test-token-123'
      }
    }))

    mockUseWebSocket.mockReturnValue({
      isConnected: true,
      isConnecting: false,
      error: null,
      reconnectAttempts: 0,
      connect: vi.fn(),
      disconnect: vi.fn(),
      sendMessage: mockSendMessage,
    })
  })

  afterEach(() => {
    localStorage.clear()
  })

  describe('WebSocket connection', () => {
    it('should connect to WebSocket with token from localStorage', () => {
      renderHook(() => useRealTimeUpdates())

      expect(mockUseWebSocket).toHaveBeenCalled()
      const callArgs = mockUseWebSocket.mock.calls[0][0]
      expect(callArgs.url).toContain('test-token-123')
    })

    it('should not connect when no token is available', () => {
      localStorage.clear()

      renderHook(() => useRealTimeUpdates())

      expect(mockUseWebSocket).toHaveBeenCalled()
      const callArgs = mockUseWebSocket.mock.calls[0][0]
      expect(callArgs.url).toBeNull()
    })

    it('should return connection state', () => {
      const { result } = renderHook(() => useRealTimeUpdates())

      expect(result.current.isConnected).toBe(true)
      expect(result.current.isConnecting).toBe(false)
      expect(result.current.error).toBeNull()
    })
  })

  describe('message handling', () => {
    it('should invalidate images queries on image_uploaded', () => {
      renderHook(() => useRealTimeUpdates())

      // Get the onMessage handler from the hook
      const callArgs = mockUseWebSocket.mock.calls[0][0]
      const onMessage = callArgs.onMessage

      if (onMessage) {
        onMessage({
          type: 'image_uploaded',
          data: { name: 'test-image.vhdx' },
          timestamp: new Date().toISOString(),
        })
      }

      expect(mockInvalidateQueries).toHaveBeenCalledWith({ queryKey: ['images'] })
      expect(mockInvalidateQueries).toHaveBeenCalledWith({ queryKey: ['storage'] })
      expect(toast.success).toHaveBeenCalledWith(
        expect.stringContaining('uploaded successfully')
      )
    })

    it('should invalidate images queries on image_processed', () => {
      renderHook(() => useRealTimeUpdates())

      const callArgs = mockUseWebSocket.mock.calls[0][0]
      const onMessage = callArgs.onMessage

      if (onMessage) {
        onMessage({
          type: 'image_processed',
          data: { name: 'test-image.vhdx' },
          timestamp: new Date().toISOString(),
        })
      }

      expect(mockInvalidateQueries).toHaveBeenCalledWith({ queryKey: ['images'] })
      expect(toast.success).toHaveBeenCalledWith(
        expect.stringContaining('processed successfully')
      )
    })

    it('should invalidate sessions queries on session_started', () => {
      renderHook(() => useRealTimeUpdates())

      const callArgs = mockUseWebSocket.mock.calls[0][0]
      const onMessage = callArgs.onMessage

      if (onMessage) {
        onMessage({
          type: 'session_started',
          data: { machine_name: 'test-machine' },
          timestamp: new Date().toISOString(),
        })
      }

      expect(mockInvalidateQueries).toHaveBeenCalledWith({ queryKey: ['sessions'] })
      expect(mockInvalidateQueries).toHaveBeenCalledWith({ queryKey: ['machines'] })
      expect(toast.success).toHaveBeenCalledWith(
        expect.stringContaining('started')
      )
    })

    it('should invalidate sessions queries on session_ended', () => {
      renderHook(() => useRealTimeUpdates())

      const callArgs = mockUseWebSocket.mock.calls[0][0]
      const onMessage = callArgs.onMessage

      if (onMessage) {
        onMessage({
          type: 'session_ended',
          data: { machine_name: 'test-machine' },
          timestamp: new Date().toISOString(),
        })
      }

      expect(mockInvalidateQueries).toHaveBeenCalledWith({ queryKey: ['sessions'] })
      expect(toast.success).toHaveBeenCalledWith(
        expect.stringContaining('ended')
      )
    })

    it('should invalidate machines queries on machine_connected', () => {
      renderHook(() => useRealTimeUpdates())

      const callArgs = mockUseWebSocket.mock.calls[0][0]
      const onMessage = callArgs.onMessage

      if (onMessage) {
        onMessage({
          type: 'machine_connected',
          data: { name: 'test-machine' },
          timestamp: new Date().toISOString(),
        })
      }

      expect(mockInvalidateQueries).toHaveBeenCalledWith({ queryKey: ['machines'] })
      expect(mockInvalidateQueries).toHaveBeenCalledWith({ queryKey: ['health', 'detailed'] })
      expect(toast.success).toHaveBeenCalledWith(
        expect.stringContaining('connected')
      )
    })

    it('should invalidate machines queries on machine_disconnected', () => {
      renderHook(() => useRealTimeUpdates())

      const callArgs = mockUseWebSocket.mock.calls[0][0]
      const onMessage = callArgs.onMessage

      if (onMessage) {
        onMessage({
          type: 'machine_disconnected',
          data: { name: 'test-machine' },
          timestamp: new Date().toISOString(),
        })
      }

      expect(mockInvalidateQueries).toHaveBeenCalledWith({ queryKey: ['machines'] })
      expect(toast.success).toHaveBeenCalledWith(
        expect.stringContaining('disconnected')
      )
    })

    it('should invalidate all queries on unknown update type', () => {
      renderHook(() => useRealTimeUpdates())

      const callArgs = mockUseWebSocket.mock.calls[0][0]
      const onMessage = callArgs.onMessage

      if (onMessage) {
        onMessage({
          type: 'unknown_type' as unknown as string,
          data: {},
          timestamp: new Date().toISOString(),
        })
      }

      expect(mockInvalidateQueries).toHaveBeenCalledWith()
    })
  })

  describe('sendUpdate', () => {
    it('should send update message via WebSocket', () => {
      const { result } = renderHook(() => useRealTimeUpdates())

      result.current.sendUpdate('test_type', { key: 'value' })

      expect(mockSendMessage).toHaveBeenCalledWith({
        type: 'test_type',
        data: { key: 'value' },
        timestamp: expect.any(String),
      })
    })

    it('should include timestamp in update message', () => {
      const { result } = renderHook(() => useRealTimeUpdates())

      result.current.sendUpdate('test_type', {})

      expect(mockSendMessage).toHaveBeenCalledWith({
        type: 'test_type',
        data: {},
        timestamp: expect.stringMatching(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/),
      })
    })
  })

  describe('error handling', () => {
    it('should handle WebSocket errors', () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
      
      renderHook(() => useRealTimeUpdates())

      const callArgs = mockUseWebSocket.mock.calls[0][0]
      const onError = callArgs.onError

      if (onError) {
        onError(new Event('error'))
      }

      expect(consoleErrorSpy).toHaveBeenCalled()
      consoleErrorSpy.mockRestore()
    })

    it('should handle invalid localStorage data gracefully', () => {
      localStorage.setItem('auth-storage', 'invalid json')

      renderHook(() => useRealTimeUpdates())

      expect(mockUseWebSocket).toHaveBeenCalled()
      const callArgs = mockUseWebSocket.mock.calls[0][0]
      expect(callArgs.url).toBeNull()
    })
  })
})

