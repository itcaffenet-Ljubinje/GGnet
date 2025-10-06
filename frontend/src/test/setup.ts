import '@testing-library/jest-dom'
// vi is available globally

// Mock window.matchMedia
(window as any).matchMedia = vi.fn().mockImplementation((query: string) => ({
  matches: false,
  media: query,
  onchange: null,
  addListener: vi.fn(),
  removeListener: vi.fn(),
  addEventListener: vi.fn(),
  removeEventListener: vi.fn(),
  dispatchEvent: vi.fn(),
}))

// Mock ResizeObserver
const resizeObserverMock = vi.fn().mockImplementation(() => ({ observe: vi.fn(), unobserve: vi.fn(), disconnect: vi.fn() }))
;(global as any).ResizeObserver = resizeObserverMock

// Mock IntersectionObserver
const intersectionObserverMock = vi.fn().mockImplementation(() => ({ observe: vi.fn(), unobserve: vi.fn(), disconnect: vi.fn() }))
;(global as any).IntersectionObserver = intersectionObserverMock
