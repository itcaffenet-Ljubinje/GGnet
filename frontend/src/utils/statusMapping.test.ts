// Vitest globals are available via globals: true in vitest.config.ts
import { mapBackendToFrontendStatus, getStatusText, type BackendStatus } from './statusMapping'

describe('statusMapping', () => {
  describe('mapBackendToFrontendStatus', () => {
    it('should map success statuses to "success"', () => {
      expect(mapBackendToFrontendStatus('READY')).toBe('success')
      expect(mapBackendToFrontendStatus('SUCCESS')).toBe('success')
      expect(mapBackendToFrontendStatus('UP')).toBe('success')
      expect(mapBackendToFrontendStatus('RUNNING')).toBe('success')
      expect(mapBackendToFrontendStatus('COMPLETED')).toBe('success')
    })

    it('should map info statuses to "info"', () => {
      expect(mapBackendToFrontendStatus('PROCESSING')).toBe('info')
      expect(mapBackendToFrontendStatus('UPLOADING')).toBe('info')
      expect(mapBackendToFrontendStatus('PENDING')).toBe('info')
      expect(mapBackendToFrontendStatus('BOOTING')).toBe('info')
      expect(mapBackendToFrontendStatus('IN_PROGRESS')).toBe('info')
    })

    it('should map error statuses to "error"', () => {
      expect(mapBackendToFrontendStatus('ERROR')).toBe('error')
      expect(mapBackendToFrontendStatus('FAILED')).toBe('error')
      expect(mapBackendToFrontendStatus('DOWN')).toBe('error')
    })

    it('should map warning status to "warning"', () => {
      expect(mapBackendToFrontendStatus('WARNING')).toBe('warning')
    })

    it('should map inactive statuses to "inactive"', () => {
      expect(mapBackendToFrontendStatus('STOPPED')).toBe('inactive')
      expect(mapBackendToFrontendStatus('IDLE')).toBe('inactive')
      expect(mapBackendToFrontendStatus('INACTIVE')).toBe('inactive')
    })

    it('should default to "info" for unknown statuses', () => {
      // TypeScript won't allow this, but runtime might
      expect(mapBackendToFrontendStatus('UNKNOWN' as BackendStatus)).toBe('info')
    })
  })

  describe('getStatusText', () => {
    it('should return correct text for all known statuses', () => {
      expect(getStatusText('READY')).toBe('Ready')
      expect(getStatusText('PROCESSING')).toBe('Processing')
      expect(getStatusText('ERROR')).toBe('Error')
      expect(getStatusText('UPLOADING')).toBe('Uploading')
      expect(getStatusText('PENDING')).toBe('Pending')
      expect(getStatusText('COMPLETED')).toBe('Completed')
      expect(getStatusText('FAILED')).toBe('Failed')
      expect(getStatusText('RUNNING')).toBe('Running')
      expect(getStatusText('STOPPED')).toBe('Stopped')
      expect(getStatusText('WARNING')).toBe('Warning')
      expect(getStatusText('SUCCESS')).toBe('Success')
      expect(getStatusText('IDLE')).toBe('Idle')
      expect(getStatusText('BOOTING')).toBe('Booting')
      expect(getStatusText('IN_PROGRESS')).toBe('In Progress')
      expect(getStatusText('UP')).toBe('Up')
      expect(getStatusText('DOWN')).toBe('Down')
    })

    it('should return the status string for unknown statuses', () => {
      const unknownStatus = 'UNKNOWN_STATUS' as BackendStatus
      expect(getStatusText(unknownStatus)).toBe('UNKNOWN_STATUS')
    })
  })

  describe('integration', () => {
    it('should handle all status types consistently', () => {
      const statuses: BackendStatus[] = [
        'READY', 'PROCESSING', 'ERROR', 'UPLOADING', 'PENDING',
        'COMPLETED', 'FAILED', 'RUNNING', 'STOPPED', 'WARNING',
        'SUCCESS', 'IDLE', 'BOOTING', 'IN_PROGRESS', 'UP', 'DOWN', 'INACTIVE'
      ]

      statuses.forEach(status => {
        const frontendStatus = mapBackendToFrontendStatus(status)
        const statusText = getStatusText(status)
        
        expect(frontendStatus).toBeTruthy()
        expect(statusText).toBeTruthy()
        expect(typeof frontendStatus).toBe('string')
        expect(typeof statusText).toBe('string')
      })
    })
  })
})

