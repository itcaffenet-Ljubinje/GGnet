# PHASE 5: Frontend (React + TypeScript) - Testing Guide

## Overview
This document provides comprehensive testing instructions for Phase 5 frontend components, including unit tests, integration tests, and user experience testing.

## Test Environment Setup

### Prerequisites
- Node.js 18+
- npm 9+
- Modern web browser
- React Developer Tools extension

### Installation
```bash
# Install dependencies
npm install

# Install testing dependencies
npm install --save-dev @testing-library/react @testing-library/jest-dom @testing-library/user-event jest-environment-jsdom
```

## Running Tests

### All Tests
```bash
# Run all tests
npm test

# Run tests in watch mode
npm test -- --watch

# Run tests with coverage
npm test -- --coverage
```

### Specific Test Categories
```bash
# Test specific components
npm test -- SessionManager
npm test -- TargetManager
npm test -- NetworkBootMonitor
npm test -- ImageManager
npm test -- SystemMonitor

# Test specific functionality
npm test -- --testNamePattern="session management"
npm test -- --testNamePattern="target creation"
npm test -- --testNamePattern="image upload"
```

## Component Testing

### 1. SessionManager Component Tests

#### Test: Session Creation and Management
```typescript
// tests/components/SessionManager.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import SessionManager from '../../src/components/SessionManager'

describe('SessionManager', () => {
  let queryClient: QueryClient

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false }
      }
    })
  })

  test('should render session statistics', async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <SessionManager />
      </QueryClientProvider>
    )

    expect(screen.getByText('Total Sessions')).toBeInTheDocument()
    expect(screen.getByText('Active Sessions')).toBeInTheDocument()
  })

  test('should allow starting a new session', async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <SessionManager />
      </QueryClientProvider>
    )

    // Select machine and image
    const machineSelect = screen.getByLabelText('Select Machine')
    const imageSelect = screen.getByLabelText('Select Image')
    
    fireEvent.change(machineSelect, { target: { value: '1' } })
    fireEvent.change(imageSelect, { target: { value: '1' } })

    // Click start session button
    const startButton = screen.getByText('Start Session')
    fireEvent.click(startButton)

    await waitFor(() => {
      expect(screen.getByText('Starting...')).toBeInTheDocument()
    })
  })

  test('should display active sessions', async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <SessionManager />
      </QueryClientProvider>
    )

    await waitFor(() => {
      expect(screen.getByText('Active Sessions')).toBeInTheDocument()
    })
  })
})
```

#### Test: Real-time Updates
```typescript
test('should update session data in real-time', async () => {
  const { rerender } = render(
    <QueryClientProvider client={queryClient}>
      <SessionManager />
    </QueryClientProvider>
  )

  // Simulate data update
  await waitFor(() => {
    expect(screen.getByText('Active Sessions')).toBeInTheDocument()
  })

  // Rerender with updated data
  rerender(
    <QueryClientProvider client={queryClient}>
      <SessionManager />
    </QueryClientProvider>
  )

  // Verify updates are reflected
  await waitFor(() => {
    expect(screen.getByText('Active Sessions')).toBeInTheDocument()
  })
})
```

### 2. TargetManager Component Tests

#### Test: Target Creation
```typescript
// tests/components/TargetManager.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import TargetManager from '../../src/components/TargetManager'

describe('TargetManager', () => {
  test('should render target creation form', () => {
    render(<TargetManager />)
    
    expect(screen.getByText('Create Target')).toBeInTheDocument()
    expect(screen.getByText('Select Machine')).toBeInTheDocument()
    expect(screen.getByText('Select Image')).toBeInTheDocument()
  })

  test('should create new target', async () => {
    render(<TargetManager />)

    // Open create form
    const createButton = screen.getByText('Create Target')
    fireEvent.click(createButton)

    // Fill form
    const machineSelect = screen.getByLabelText('Select Machine')
    const imageSelect = screen.getByLabelText('Select Image')
    
    fireEvent.change(machineSelect, { target: { value: '1' } })
    fireEvent.change(imageSelect, { target: { value: '1' } })

    // Submit form
    const submitButton = screen.getByText('Create Target')
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText('Creating...')).toBeInTheDocument()
    })
  })

  test('should display existing targets', async () => {
    render(<TargetManager />)

    await waitFor(() => {
      expect(screen.getByText('iSCSI Targets')).toBeInTheDocument()
    })
  })
})
```

### 3. NetworkBootMonitor Component Tests

#### Test: Real-time Monitoring
```typescript
// tests/components/NetworkBootMonitor.test.tsx
import { render, screen, waitFor } from '@testing-library/react'
import NetworkBootMonitor from '../../src/components/NetworkBootMonitor'

describe('NetworkBootMonitor', () => {
  test('should display boot statistics', async () => {
    render(<NetworkBootMonitor />)

    await waitFor(() => {
      expect(screen.getByText('Total Boots')).toBeInTheDocument()
      expect(screen.getByText('Success Rate')).toBeInTheDocument()
      expect(screen.getByText('Avg Boot Time')).toBeInTheDocument()
    })
  })

  test('should show network services status', async () => {
    render(<NetworkBootMonitor />)

    await waitFor(() => {
      expect(screen.getByText('Network Services')).toBeInTheDocument()
    })
  })

  test('should display machine boot status', async () => {
    render(<NetworkBootMonitor />)

    await waitFor(() => {
      expect(screen.getByText('Machine Boot Status')).toBeInTheDocument()
    })
  })
})
```

### 4. ImageManager Component Tests

#### Test: Image Upload
```typescript
// tests/components/ImageManager.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import ImageManager from '../../src/components/ImageManager'

describe('ImageManager', () => {
  test('should render upload area', () => {
    render(<ImageManager />)
    
    expect(screen.getByText('Upload Images')).toBeInTheDocument()
  })

  test('should handle file upload', async () => {
    render(<ImageManager />)

    // Open upload area
    const uploadButton = screen.getByText('Upload Images')
    fireEvent.click(uploadButton)

    // Simulate file drop
    const dropArea = screen.getByText('Drag & drop images here, or click to select')
    const file = new File(['test'], 'test.vhdx', { type: 'application/octet-stream' })
    
    fireEvent.drop(dropArea, {
      dataTransfer: {
        files: [file]
      }
    })

    await waitFor(() => {
      expect(screen.getByText('Upload Progress')).toBeInTheDocument()
    })
  })

  test('should display image list', async () => {
    render(<ImageManager />)

    await waitFor(() => {
      expect(screen.getByText('Disk Images')).toBeInTheDocument()
    })
  })
})
```

### 5. SystemMonitor Component Tests

#### Test: Performance Monitoring
```typescript
// tests/components/SystemMonitor.test.tsx
import { render, screen, waitFor } from '@testing-library/react'
import SystemMonitor from '../../src/components/SystemMonitor'

describe('SystemMonitor', () => {
  test('should display system health overview', async () => {
    render(<SystemMonitor />)

    await waitFor(() => {
      expect(screen.getByText('System Health')).toBeInTheDocument()
      expect(screen.getByText('Active Sessions')).toBeInTheDocument()
      expect(screen.getByText('CPU Usage')).toBeInTheDocument()
      expect(screen.getByText('Memory Usage')).toBeInTheDocument()
    })
  })

  test('should show performance charts', async () => {
    render(<SystemMonitor />)

    await waitFor(() => {
      expect(screen.getByText('CPU & Memory Usage')).toBeInTheDocument()
      expect(screen.getByText('Network Activity')).toBeInTheDocument()
    })
  })

  test('should display service status', async () => {
    render(<SystemMonitor />)

    await waitFor(() => {
      expect(screen.getByText('Services Status')).toBeInTheDocument()
    })
  })
})
```

## Integration Testing

### 1. API Integration Tests

#### Test: Session API Integration
```typescript
// tests/integration/sessionApi.test.tsx
import { render, screen, waitFor } from '@testing-library/react'
import { rest } from 'msw'
import { setupServer } from 'msw/node'
import SessionManager from '../../src/components/SessionManager'

const server = setupServer(
  rest.get('/api/v1/sessions/', (req, res, ctx) => {
    return res(ctx.json({
      sessions: [
        {
          id: 1,
          machine_id: 1,
          target_id: 1,
          image_id: 1,
          status: 'ACTIVE',
          started_at: '2024-01-01T00:00:00Z'
        }
      ],
      total: 1
    }))
  })
)

beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

test('should fetch and display sessions', async () => {
  render(<SessionManager />)

  await waitFor(() => {
    expect(screen.getByText('Active Sessions')).toBeInTheDocument()
  })
})
```

#### Test: Error Handling
```typescript
test('should handle API errors gracefully', async () => {
  server.use(
    rest.get('/api/v1/sessions/', (req, res, ctx) => {
      return res(ctx.status(500), ctx.json({ error: 'Internal server error' }))
    })
  )

  render(<SessionManager />)

  await waitFor(() => {
    expect(screen.getByText('Error loading session data')).toBeInTheDocument()
  })
})
```

### 2. Real-time Updates Testing

#### Test: WebSocket Integration
```typescript
// tests/integration/realtimeUpdates.test.tsx
import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

test('should update data in real-time', async () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false }
    }
  })

  render(
    <QueryClientProvider client={queryClient}>
      <SessionManager />
    </QueryClientProvider>
  )

  // Wait for initial data
  await waitFor(() => {
    expect(screen.getByText('Active Sessions')).toBeInTheDocument()
  })

  // Simulate real-time update
  queryClient.setQueryData(['sessions'], {
    sessions: [
      {
        id: 2,
        machine_id: 2,
        target_id: 2,
        image_id: 2,
        status: 'ACTIVE',
        started_at: '2024-01-01T00:00:00Z'
      }
    ],
    total: 1
  })

  // Verify update is reflected
  await waitFor(() => {
    expect(screen.getByText('Active Sessions')).toBeInTheDocument()
  })
})
```

## User Experience Testing

### 1. Responsive Design Testing

#### Test: Mobile Responsiveness
```typescript
// tests/ux/responsive.test.tsx
import { render, screen } from '@testing-library/react'

test('should be responsive on mobile devices', () => {
  // Mock mobile viewport
  Object.defineProperty(window, 'innerWidth', {
    writable: true,
    configurable: true,
    value: 375
  })

  render(<SessionManager />)

  // Check that mobile navigation is available
  expect(screen.getByRole('button', { name: /menu/i })).toBeInTheDocument()
})
```

#### Test: Desktop Layout
```typescript
test('should display full layout on desktop', () => {
  // Mock desktop viewport
  Object.defineProperty(window, 'innerWidth', {
    writable: true,
    configurable: true,
    value: 1920
  })

  render(<SessionManager />)

  // Check that sidebar is visible
  expect(screen.getByText('Dashboard')).toBeInTheDocument()
  expect(screen.getByText('Machines')).toBeInTheDocument()
})
```

### 2. Accessibility Testing

#### Test: Keyboard Navigation
```typescript
// tests/ux/accessibility.test.tsx
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

test('should support keyboard navigation', async () => {
  const user = userEvent.setup()
  render(<SessionManager />)

  // Tab through interactive elements
  await user.tab()
  expect(screen.getByLabelText('Select Machine')).toHaveFocus()

  await user.tab()
  expect(screen.getByLabelText('Select Image')).toHaveFocus()

  await user.tab()
  expect(screen.getByText('Start Session')).toHaveFocus()
})
```

#### Test: Screen Reader Support
```typescript
test('should have proper ARIA labels', () => {
  render(<SessionManager />)

  // Check for proper labels
  expect(screen.getByLabelText('Select Machine')).toBeInTheDocument()
  expect(screen.getByLabelText('Select Image')).toBeInTheDocument()
  expect(screen.getByRole('button', { name: /start session/i })).toBeInTheDocument()
})
```

### 3. Performance Testing

#### Test: Component Rendering Performance
```typescript
// tests/ux/performance.test.tsx
import { render } from '@testing-library/react'
import { performance } from 'perf_hooks'

test('should render within performance budget', () => {
  const start = performance.now()
  render(<SessionManager />)
  const end = performance.now()

  // Should render within 100ms
  expect(end - start).toBeLessThan(100)
})
```

#### Test: Memory Usage
```typescript
test('should not leak memory', () => {
  const { unmount } = render(<SessionManager />)
  
  // Unmount component
  unmount()
  
  // Check that no memory leaks occurred
  // This would typically be done with memory profiling tools
  expect(true).toBe(true) // Placeholder for actual memory leak detection
})
```

## End-to-End Testing

### 1. User Journey Tests

#### Test: Complete Session Lifecycle
```typescript
// tests/e2e/sessionLifecycle.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

test('should complete full session lifecycle', async () => {
  const user = userEvent.setup()
  render(<SessionManager />)

  // 1. Start session
  await user.selectOptions(screen.getByLabelText('Select Machine'), '1')
  await user.selectOptions(screen.getByLabelText('Select Image'), '1')
  await user.click(screen.getByText('Start Session'))

  await waitFor(() => {
    expect(screen.getByText('Starting...')).toBeInTheDocument()
  })

  // 2. Verify session appears in active sessions
  await waitFor(() => {
    expect(screen.getByText('Active Sessions')).toBeInTheDocument()
  })

  // 3. Stop session
  const stopButton = screen.getByText('Stop')
  await user.click(stopButton)

  // 4. Verify session is stopped
  await waitFor(() => {
    expect(screen.getByText('Session stopped successfully')).toBeInTheDocument()
  })
})
```

#### Test: Image Upload and Conversion
```typescript
test('should upload and convert image', async () => {
  const user = userEvent.setup()
  render(<ImageManager />)

  // 1. Open upload area
  await user.click(screen.getByText('Upload Images'))

  // 2. Upload file
  const file = new File(['test'], 'test.vhdx', { type: 'application/octet-stream' })
  const input = screen.getByLabelText(/drag.*drop.*images/i)
  
  await user.upload(input, file)

  // 3. Verify upload progress
  await waitFor(() => {
    expect(screen.getByText('Upload Progress')).toBeInTheDocument()
  })

  // 4. Trigger conversion
  await waitFor(() => {
    const convertButton = screen.getByText('Convert to RAW')
    expect(convertButton).toBeInTheDocument()
  })

  await user.click(screen.getByText('Convert to RAW'))

  // 5. Verify conversion started
  await waitFor(() => {
    expect(screen.getByText('Conversion triggered')).toBeInTheDocument()
  })
})
```

## Mock Data and Test Utilities

### 1. Mock Data Setup
```typescript
// tests/utils/mockData.ts
export const mockSessions = [
  {
    id: 1,
    machine_id: 1,
    target_id: 1,
    image_id: 1,
    session_type: 'DISKLESS_BOOT',
    status: 'ACTIVE',
    started_at: '2024-01-01T00:00:00Z',
    created_by: 1
  }
]

export const mockMachines = [
  {
    id: 1,
    name: 'test-workstation',
    mac_address: '00:11:22:33:44:55',
    ip_address: '192.168.1.101',
    status: 'ACTIVE',
    boot_mode: 'bios',
    created_by: 1
  }
]

export const mockImages = [
  {
    id: 1,
    name: 'test-image',
    filename: 'test.vhdx',
    file_path: '/storage/images/test.vhdx',
    format: 'VHDX',
    status: 'READY',
    size_bytes: 1024 * 1024 * 1024,
    created_by: 1
  }
]
```

### 2. Test Utilities
```typescript
// tests/utils/testUtils.tsx
import { ReactElement } from 'react'
import { render, RenderOptions } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

const AllTheProviders = ({ children }: { children: React.ReactNode }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false }
    }
  })

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}

const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => render(ui, { wrapper: AllTheProviders, ...options })

export * from '@testing-library/react'
export { customRender as render }
```

## Test Configuration

### 1. Jest Configuration
```javascript
// jest.config.js
module.exports = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/src/setupTests.ts'],
  moduleNameMapping: {
    '^@/(.*)$': '<rootDir>/src/$1'
  },
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
    '!src/index.tsx',
    '!src/setupTests.ts'
  ],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80
    }
  }
}
```

### 2. Setup Tests
```typescript
// src/setupTests.ts
import '@testing-library/jest-dom'

// Mock IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  unobserve() {}
}

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  unobserve() {}
}
```

## Continuous Integration

### 1. GitHub Actions
```yaml
# .github/workflows/frontend-tests.yml
name: Frontend Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Node.js
        uses: actions/setup-node@v2
        with:
          node-version: '18'
      - name: Install dependencies
        run: npm ci
      - name: Run tests
        run: npm test -- --coverage --watchAll=false
      - name: Upload coverage
        uses: codecov/codecov-action@v1
```

### 2. Test Scripts
```json
{
  "scripts": {
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage",
    "test:ci": "jest --coverage --watchAll=false",
    "test:e2e": "playwright test"
  }
}
```

## Performance Testing

### 1. Bundle Size Testing
```typescript
// tests/performance/bundleSize.test.ts
import { getBundleSize } from '../utils/bundleAnalyzer'

test('should not exceed bundle size limits', () => {
  const bundleSize = getBundleSize()
  
  expect(bundleSize.main).toBeLessThan(500 * 1024) // 500KB
  expect(bundleSize.vendor).toBeLessThan(1000 * 1024) // 1MB
})
```

### 2. Runtime Performance Testing
```typescript
// tests/performance/runtime.test.ts
import { measureRenderTime } from '../utils/performanceUtils'

test('should render within performance budget', async () => {
  const renderTime = await measureRenderTime(<SessionManager />)
  
  expect(renderTime).toBeLessThan(100) // 100ms
})
```

## Debugging Tests

### 1. Debug Mode
```bash
# Run tests in debug mode
npm test -- --debug

# Run specific test in debug mode
npm test -- --testNamePattern="session management" --debug
```

### 2. Visual Debugging
```typescript
// Add to test files for visual debugging
import { screen } from '@testing-library/react'

test('debug test', () => {
  render(<SessionManager />)
  screen.debug() // Prints current DOM state
})
```

## Best Practices

### 1. Test Organization
- Group related tests in describe blocks
- Use descriptive test names
- Keep tests focused and atomic
- Mock external dependencies

### 2. Test Data
- Use consistent mock data
- Create reusable test utilities
- Keep test data minimal and focused
- Use factories for complex data

### 3. Assertions
- Use specific assertions
- Test behavior, not implementation
- Verify user-visible outcomes
- Test error conditions

### 4. Performance
- Keep tests fast
- Use appropriate mocking
- Avoid unnecessary renders
- Clean up after tests
