// Vitest globals are available via globals: true in vitest.config.ts
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { api, apiHelpers } from './api'

// Mock axios
vi.mock('axios', async () => {
  const actual = await vi.importActual('axios')
  return {
    ...actual,
    create: vi.fn(() => ({
      get: vi.fn(),
      post: vi.fn(),
      put: vi.fn(),
      delete: vi.fn(),
      interceptors: {
        request: { use: vi.fn(), handlers: [] },
        response: { use: vi.fn(), handlers: [] },
      },
      defaults: {
        baseURL: '',
        timeout: 30000,
        headers: { 'Content-Type': 'application/json' },
      },
    })),
  }
})

describe('api', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('api instance', () => {
    it('should export api instance', () => {
      expect(api).toBeDefined()
      expect(api.defaults).toBeDefined()
    })

    it('should have default timeout', () => {
      expect(api.defaults.timeout).toBe(30000)
    })
  })

  describe('apiHelpers', () => {
    describe('auth helpers', () => {
      it('should have login helper', () => {
        expect(apiHelpers.login).toBeDefined()
        expect(typeof apiHelpers.login).toBe('function')
      })

      it('should have logout helper', () => {
        expect(apiHelpers.logout).toBeDefined()
        expect(typeof apiHelpers.logout).toBe('function')
      })

      it('should have refreshToken helper', () => {
        expect(apiHelpers.refreshToken).toBeDefined()
        expect(typeof apiHelpers.refreshToken).toBe('function')
      })

      it('should have getCurrentUser helper', () => {
        expect(apiHelpers.getCurrentUser).toBeDefined()
        expect(typeof apiHelpers.getCurrentUser).toBe('function')
      })

      it('should have changePassword helper', () => {
        expect(apiHelpers.changePassword).toBeDefined()
        expect(typeof apiHelpers.changePassword).toBe('function')
      })
    })

    describe('image helpers', () => {
      it('should have getImages helper', () => {
        expect(apiHelpers.getImages).toBeDefined()
        expect(typeof apiHelpers.getImages).toBe('function')
      })

      it('should have getImage helper', () => {
        expect(apiHelpers.getImage).toBeDefined()
        expect(typeof apiHelpers.getImage).toBe('function')
      })

      it('should have uploadImage helper', () => {
        expect(apiHelpers.uploadImage).toBeDefined()
        expect(typeof apiHelpers.uploadImage).toBe('function')
      })

      it('should have updateImage helper', () => {
        expect(apiHelpers.updateImage).toBeDefined()
        expect(typeof apiHelpers.updateImage).toBe('function')
      })

      it('should have deleteImage helper', () => {
        expect(apiHelpers.deleteImage).toBeDefined()
        expect(typeof apiHelpers.deleteImage).toBe('function')
      })
    })

    describe('machine helpers', () => {
      it('should have getMachines helper', () => {
        expect(apiHelpers.getMachines).toBeDefined()
        expect(typeof apiHelpers.getMachines).toBe('function')
      })

      it('should have getMachine helper', () => {
        expect(apiHelpers.getMachine).toBeDefined()
        expect(typeof apiHelpers.getMachine).toBe('function')
      })

      it('should have createMachine helper', () => {
        expect(apiHelpers.createMachine).toBeDefined()
        expect(typeof apiHelpers.createMachine).toBe('function')
      })

      it('should have updateMachine helper', () => {
        expect(apiHelpers.updateMachine).toBeDefined()
        expect(typeof apiHelpers.updateMachine).toBe('function')
      })

      it('should have deleteMachine helper', () => {
        expect(apiHelpers.deleteMachine).toBeDefined()
        expect(typeof apiHelpers.deleteMachine).toBe('function')
      })
    })

    describe('target helpers', () => {
      it('should have getTargets helper', () => {
        expect(apiHelpers.getTargets).toBeDefined()
        expect(typeof apiHelpers.getTargets).toBe('function')
      })

      it('should have getTarget helper', () => {
        expect(apiHelpers.getTarget).toBeDefined()
        expect(typeof apiHelpers.getTarget).toBe('function')
      })

      it('should have createTarget helper', () => {
        expect(apiHelpers.createTarget).toBeDefined()
        expect(typeof apiHelpers.createTarget).toBe('function')
      })

      it('should have updateTarget helper', () => {
        expect(apiHelpers.updateTarget).toBeDefined()
        expect(typeof apiHelpers.updateTarget).toBe('function')
      })

      it('should have deleteTarget helper', () => {
        expect(apiHelpers.deleteTarget).toBeDefined()
        expect(typeof apiHelpers.deleteTarget).toBe('function')
      })
    })

    describe('session helpers', () => {
      it('should have getSessions helper', () => {
        expect(apiHelpers.getSessions).toBeDefined()
        expect(typeof apiHelpers.getSessions).toBe('function')
      })

      it('should have getSessionStatus helper', () => {
        expect(apiHelpers.getSessionStatus).toBeDefined()
        expect(typeof apiHelpers.getSessionStatus).toBe('function')
      })

      it('should have startSession helper', () => {
        expect(apiHelpers.startSession).toBeDefined()
        expect(typeof apiHelpers.startSession).toBe('function')
      })

      it('should have stopSession helper', () => {
        expect(apiHelpers.stopSession).toBeDefined()
        expect(typeof apiHelpers.stopSession).toBe('function')
      })
    })

    describe('storage helpers', () => {
      it('should have getStorageInfo helper', () => {
        expect(apiHelpers.getStorageInfo).toBeDefined()
        expect(typeof apiHelpers.getStorageInfo).toBe('function')
      })

      it('should have getStorageMounts helper', () => {
        expect(apiHelpers.getStorageMounts).toBeDefined()
        expect(typeof apiHelpers.getStorageMounts).toBe('function')
      })

      it('should have getStorageHealth helper', () => {
        expect(apiHelpers.getStorageHealth).toBeDefined()
        expect(typeof apiHelpers.getStorageHealth).toBe('function')
      })

      it('should have cleanupStorage helper', () => {
        expect(apiHelpers.cleanupStorage).toBeDefined()
        expect(typeof apiHelpers.cleanupStorage).toBe('function')
      })
    })

    describe('ZFS helpers', () => {
      it('should have getZfsPools helper', () => {
        expect(apiHelpers.getZfsPools).toBeDefined()
        expect(typeof apiHelpers.getZfsPools).toBe('function')
      })

      it('should have getZfsDatasets helper', () => {
        expect(apiHelpers.getZfsDatasets).toBeDefined()
        expect(typeof apiHelpers.getZfsDatasets).toBe('function')
      })

      it('should have getZfsSnapshots helper', () => {
        expect(apiHelpers.getZfsSnapshots).toBeDefined()
        expect(typeof apiHelpers.getZfsSnapshots).toBe('function')
      })
    })

    describe('health helpers', () => {
      it('should have getHealth helper', () => {
        expect(apiHelpers.getHealth).toBeDefined()
        expect(typeof apiHelpers.getHealth).toBe('function')
      })

      it('should have getDetailedHealth helper', () => {
        expect(apiHelpers.getDetailedHealth).toBeDefined()
        expect(typeof apiHelpers.getDetailedHealth).toBe('function')
      })
    })

    describe('monitoring helpers', () => {
      it('should have getPerformanceMetrics helper', () => {
        expect(apiHelpers.getPerformanceMetrics).toBeDefined()
        expect(typeof apiHelpers.getPerformanceMetrics).toBe('function')
      })

      it('should have getActiveSessions helper', () => {
        expect(apiHelpers.getActiveSessions).toBeDefined()
        expect(typeof apiHelpers.getActiveSessions).toBe('function')
      })

      it('should have getSessionStats helper', () => {
        expect(apiHelpers.getSessionStats).toBeDefined()
        expect(typeof apiHelpers.getSessionStats).toBe('function')
      })
    })
  })
})
