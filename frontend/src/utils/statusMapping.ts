// Utility functions to map between different status types

export type BackendStatus = 
  | 'READY' | 'PROCESSING' | 'ERROR' | 'UPLOADING' | 'PENDING' | 'COMPLETED' | 'FAILED'
  | 'RUNNING' | 'STOPPED' | 'WARNING' | 'SUCCESS' | 'IDLE' | 'BOOTING' | 'IN_PROGRESS'
  | 'UP' | 'DOWN'

export type FrontendStatus = 'active' | 'inactive' | 'error' | 'warning' | 'info' | 'success'

export function mapBackendToFrontendStatus(status: BackendStatus): FrontendStatus {
  switch (status) {
    case 'READY':
    case 'SUCCESS':
    case 'UP':
    case 'RUNNING':
    case 'COMPLETED':
      return 'success'
    case 'PROCESSING':
    case 'UPLOADING':
    case 'PENDING':
    case 'BOOTING':
    case 'IN_PROGRESS':
      return 'info'
    case 'ERROR':
    case 'FAILED':
    case 'DOWN':
      return 'error'
    case 'WARNING':
      return 'warning'
    case 'STOPPED':
    case 'IDLE':
    case 'INACTIVE':
      return 'inactive'
    default:
      return 'info'
  }
}

export function getStatusText(status: BackendStatus): string {
  switch (status) {
    case 'READY':
      return 'Ready'
    case 'PROCESSING':
      return 'Processing'
    case 'ERROR':
      return 'Error'
    case 'UPLOADING':
      return 'Uploading'
    case 'PENDING':
      return 'Pending'
    case 'COMPLETED':
      return 'Completed'
    case 'FAILED':
      return 'Failed'
    case 'RUNNING':
      return 'Running'
    case 'STOPPED':
      return 'Stopped'
    case 'WARNING':
      return 'Warning'
    case 'SUCCESS':
      return 'Success'
    case 'IDLE':
      return 'Idle'
    case 'BOOTING':
      return 'Booting'
    case 'IN_PROGRESS':
      return 'In Progress'
    case 'UP':
      return 'Up'
    case 'DOWN':
      return 'Down'
    default:
      return status
  }
}
