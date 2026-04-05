/**
 * Mock Data Factories
 * 
 * Centralized factories for creating test data
 * Ensures consistent test data across all tests
 */

import type { User } from '../../stores/authStore'

/**
 * Create a mock user
 */
export const createMockUser = (overrides?: Partial<User>): User => ({
  id: 1,
  username: 'testuser',
  email: 'test@example.com',
  full_name: 'Test User',
  role: 'admin',
  status: 'active',
  is_active: true,
  created_at: '2024-01-01T00:00:00Z',
  last_login: '2024-01-01T00:00:00Z',
  ...overrides,
})

/**
 * Mock Machine interface
 */
interface MockMachine {
  id: number
  name: string
  hostname: string
  ip_address: string
  mac_address: string
  status: string
  boot_mode: string
  created_at: string
  [key: string]: unknown
}

/**
 * Create a mock machine
 */
export const createMockMachine = (overrides?: Partial<MockMachine>): MockMachine => ({
  id: 1,
  name: 'Test Machine',
  hostname: 'test-machine.local',
  ip_address: '192.168.1.100',
  mac_address: '00:11:22:33:44:55',
  status: 'active',
  boot_mode: 'UEFI',
  created_at: '2024-01-01T00:00:00Z',
  ...overrides,
})

/**
 * Mock Image interface
 */
interface MockImage {
  id: number
  name: string
  filename: string
  format: string
  status: string
  size_bytes: number
  created_at: string
  [key: string]: unknown
}

/**
 * Create a mock image
 */
export const createMockImage = (overrides?: Partial<MockImage>): MockImage => ({
  id: 1,
  name: 'Test Image',
  filename: 'test.vhdx',
  format: 'VHDX',
  status: 'READY',
  size_bytes: 1024 * 1024 * 1024, // 1GB
  created_at: '2024-01-01T00:00:00Z',
  ...overrides,
})

/**
 * Mock Session interface
 */
interface MockSession {
  id: number
  session_id: string
  machine_id: number
  target_id: number
  session_type: string
  status: string
  started_at: string
  [key: string]: unknown
}

/**
 * Create a mock session
 */
export const createMockSession = (overrides?: Partial<MockSession>): MockSession => ({
  id: 1,
  session_id: 'test-session-1',
  machine_id: 1,
  target_id: 1,
  session_type: 'DISKLESS_BOOT',
  status: 'ACTIVE',
  started_at: '2024-01-01T00:00:00Z',
  ...overrides,
})

/**
 * Mock Target interface
 */
interface MockTarget {
  id: number
  target_id: string
  iqn: string
  machine_id: number
  image_id: number
  status: string
  created_at: string
  [key: string]: unknown
}

/**
 * Create a mock target
 */
export const createMockTarget = (overrides?: Partial<MockTarget>): MockTarget => ({
  id: 1,
  target_id: 'test-target-1',
  iqn: 'iqn.2024.test:target-1',
  machine_id: 1,
  image_id: 1,
  status: 'ACTIVE',
  created_at: '2024-01-01T00:00:00Z',
  ...overrides,
})

/**
 * Create a mock API error response
 */
export const createMockError = (message: string, status: number = 400) => ({
  response: {
    status,
    data: {
      detail: message,
    },
  },
  message,
})

/**
 * Create a mock API success response
 */
export const createMockSuccessResponse = <T>(data: T, status: number = 200) => ({
  status,
  data,
})

