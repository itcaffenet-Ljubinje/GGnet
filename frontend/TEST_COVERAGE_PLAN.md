# Frontend Test Coverage Improvement Plan

## Current Status
- **Overall Coverage**: 3.17% statements, 0.79% branches, 0.75% functions, 3.53% lines
- **Test Files**: 1 (`App.test.tsx`)
- **Target Coverage**: 70%+ statements, 60%+ branches, 65%+ functions

## Priority Levels
- **P0 (Critical)**: Authentication, core utilities, error handling
- **P1 (High)**: Reusable components, hooks, stores
- **P2 (Medium)**: Page components, complex components
- **P3 (Low)**: Edge cases, optional features

---

## Phase 1: Foundation & Critical Paths (Target: 15-20% coverage)

### 1.1 Authentication & Core Store (P0)
**Files to Test:**
- `src/stores/authStore.ts` (5.55% → 80%+)
- `src/pages/LoginPage.tsx` (50% → 85%+)

**Test Cases:**
- ✅ Login success/failure scenarios
- ✅ Token storage and retrieval
- ✅ Logout functionality
- ✅ Token refresh logic
- ✅ Authentication state management
- ✅ Form validation
- ✅ Password visibility toggle
- ✅ Loading states during login

**Estimated Effort**: 4-6 hours

### 1.2 Error Handling (P0)
**Files to Test:**
- `src/components/ErrorBoundary.tsx` (26.66% → 90%+)

**Test Cases:**
- ✅ Error boundary catches React errors
- ✅ Error display UI
- ✅ Error recovery/reset
- ✅ Different error types handling

**Estimated Effort**: 2-3 hours

### 1.3 Core Utilities (P0)
**Files to Test:**
- `src/utils/statusMapping.ts` (0% → 90%+)
- `src/utils/performance.ts` (0% → 70%+)

**Test Cases:**
- ✅ Status mapping functions
- ✅ Performance monitoring utilities
- ✅ Edge cases and error handling

**Estimated Effort**: 2-3 hours

**Phase 1 Total**: ~8-12 hours | **Target Coverage**: 15-20%

---

## Phase 2: Reusable Components & Hooks (Target: 35-40% coverage)

### 2.1 UI Components (P1)
**Files to Test:**
- `src/components/ui/Button.tsx` (33.33% → 85%+)
- `src/components/ui/Input.tsx` (25% → 85%+)
- `src/components/ui/Card.tsx` (57.14% → 85%+)
- `src/components/ui/Modal.tsx` (10.52% → 85%+)
- `src/components/ui/StatusBadge.tsx` (0% → 85%+)
- `src/components/ui/ProgressBar.tsx` (0% → 85%+)
- `src/components/ui/Icon.tsx` (16.66% → 80%+)

**Test Cases:**
- ✅ Component rendering
- ✅ Props handling
- ✅ User interactions (clicks, inputs)
- ✅ Variants and states
- ✅ Accessibility attributes
- ✅ Event handlers

**Estimated Effort**: 6-8 hours

### 2.2 Loading & Feedback Components (P1)
**Files to Test:**
- `src/components/LoadingSpinner.tsx` (33.33% → 85%+)
- `src/components/notifications/index.tsx` (26% → 80%+)

**Test Cases:**
- ✅ Loading states
- ✅ Notification display
- ✅ Notification types (success, error, warning, info)
- ✅ Notification dismissal
- ✅ Auto-dismiss timing

**Estimated Effort**: 3-4 hours

### 2.3 Custom Hooks (P1)
**Files to Test:**
- `src/hooks/useWebSocket.ts` (1.29% → 75%+)
- `src/hooks/useRealTimeUpdates.ts` (2.63% → 75%+)

**Test Cases:**
- ✅ WebSocket connection/disconnection
- ✅ Message handling
- ✅ Reconnection logic
- ✅ Real-time data updates
- ✅ Error handling
- ✅ Cleanup on unmount

**Estimated Effort**: 4-6 hours

**Phase 2 Total**: ~13-18 hours | **Target Coverage**: 35-40%

---

## Phase 3: Complex Components (Target: 50-55% coverage)

### 3.1 Form & Data Components (P1)
**Files to Test:**
- `src/components/FileUpload.tsx` (0% → 70%+)
- `src/components/tables/DataTable.tsx` (0% → 75%+)

**Test Cases:**
- ✅ File selection and validation
- ✅ Upload progress
- ✅ Error handling
- ✅ Table rendering
- ✅ Sorting and filtering
- ✅ Pagination
- ✅ Row selection

**Estimated Effort**: 5-7 hours

### 3.2 Chart Components (P2)
**Files to Test:**
- `src/components/charts/UsageChart.tsx` (0% → 70%+)
- `src/components/charts/UsageChartContent.tsx` (0% → 70%+)
- `src/components/charts/NetworkChart.tsx` (0% → 70%+)
- `src/components/charts/NetworkChartContent.tsx` (0% → 70%+)

**Test Cases:**
- ✅ Chart rendering with data
- ✅ Empty state handling
- ✅ Data formatting
- ✅ Responsive behavior
- ✅ Tooltip interactions

**Estimated Effort**: 4-6 hours

### 3.3 Manager Components (P2)
**Files to Test:**
- `src/components/SessionManager.tsx` (0% → 65%+)
- `src/components/TargetManager.tsx` (0% → 65%+)
- `src/components/MachineModal.tsx` (0% → 70%+)
- `src/components/ImageManager.tsx` (0% → 65%+)

**Test Cases:**
- ✅ Component rendering
- ✅ Data fetching and display
- ✅ CRUD operations (mocked)
- ✅ Form interactions
- ✅ Modal open/close
- ✅ Error states

**Estimated Effort**: 8-10 hours

**Phase 3 Total**: ~17-23 hours | **Target Coverage**: 50-55%

---

## Phase 4: Page Components (Target: 65-70% coverage)

### 4.1 Core Pages (P1)
**Files to Test:**
- `src/pages/DashboardPage.tsx` (0% → 70%+)
- `src/pages/ImagesPage.tsx` (0% → 70%+)
- `src/pages/MachinesPage.tsx` (0% → 70%+)
- `src/pages/NotFoundPage.tsx` (0% → 90%+)

**Test Cases:**
- ✅ Page rendering
- ✅ Data loading states
- ✅ Empty states
- ✅ Error states
- ✅ Navigation
- ✅ Key user interactions

**Estimated Effort**: 8-10 hours

### 4.2 Feature Pages (P2)
**Files to Test:**
- `src/pages/SessionsPage.tsx` (0% → 65%+)
- `src/pages/TargetsPage.tsx` (0% → 65%+)
- `src/pages/SettingsPage.tsx` (0% → 65%+)
- `src/pages/ActivitiesPage.tsx` (0% → 60%+)

**Test Cases:**
- ✅ Page rendering
- ✅ Data display
- ✅ Basic interactions
- ✅ Form submissions (mocked)

**Estimated Effort**: 6-8 hours

### 4.3 Advanced Pages (P2)
**Files to Test:**
- `src/pages/MonitoringPage.tsx` (0% → 60%+)
- `src/pages/SystemMonitorPage.tsx` (0% → 60%+)
- `src/pages/NetworkBootPage.tsx` (0% → 60%+)
- `src/pages/ArrayConfigurationPage.tsx` (0% → 55%+)
- `src/pages/SnapshotsPage.tsx` (0% → 60%+)
- `src/pages/SchedulerPage.tsx` (0% → 60%+)
- `src/pages/VMsPage.tsx` (0% → 60%+)
- `src/pages/ClientsPage.tsx` (0% → 60%+)
- `src/pages/BatchOperationsPage.tsx` (0% → 55%+)
- `src/pages/WritebacksPage.tsx` (0% → 60%+)
- `src/pages/ImageImportExportPage.tsx` (0% → 55%+)

**Test Cases:**
- ✅ Page rendering
- ✅ Basic data display
- ✅ Loading states
- ✅ Error handling

**Estimated Effort**: 10-12 hours

**Phase 4 Total**: ~24-30 hours | **Target Coverage**: 65-70%

---

## Phase 5: API & Integration (Target: 70%+ coverage)

### 5.1 API Helpers (P1)
**Files to Test:**
- `src/lib/api.ts` (1.34% → 75%+)
- `src/lib/api-optimized.ts` (0% → 70%+)

**Test Cases:**
- ✅ API request/response handling
- ✅ Error handling
- ✅ Request cancellation
- ✅ Retry logic
- ✅ Token refresh
- ✅ Request deduplication (optimized)

**Estimated Effort**: 6-8 hours

### 5.2 App Integration (P1)
**Files to Test:**
- `src/App.tsx` (52.5% → 85%+)

**Test Cases:**
- ✅ Route rendering
- ✅ Authentication-based routing
- ✅ Lazy loading
- ✅ Error boundary integration
- ✅ Navigation

**Estimated Effort**: 3-4 hours

### 5.3 Complex Components (P2)
**Files to Test:**
- `src/components/SystemMonitor.tsx` (0% → 60%+)
- `src/components/NetworkBootMonitor.tsx` (0% → 60%+)

**Test Cases:**
- ✅ Component rendering
- ✅ Real-time updates (mocked)
- ✅ Data visualization
- ✅ Error handling

**Estimated Effort**: 4-6 hours

**Phase 5 Total**: ~13-18 hours | **Target Coverage**: 70%+

---

## Testing Utilities & Setup

### Required Test Utilities
- ✅ Mock API responses (`msw` or `vitest` mocks)
- ✅ Mock WebSocket connections
- ✅ Mock React Router
- ✅ Mock Zustand stores
- ✅ Test data factories
- ✅ Custom render function with providers

### Test Structure
```
src/
├── __tests__/
│   ├── setup/
│   │   ├── test-utils.tsx      # Custom render, providers
│   │   ├── mocks.ts            # Mock data factories
│   │   └── server.ts           # MSW server setup
│   └── __mocks__/
│       ├── api.ts              # API mocks
│       └── websocket.ts        # WebSocket mocks
├── components/
│   └── ui/
│       └── Button.test.tsx
├── pages/
│   └── LoginPage.test.tsx
├── stores/
│   └── authStore.test.ts
└── utils/
    └── statusMapping.test.ts
```

---

## Implementation Guidelines

### 1. Test Naming Convention
```typescript
describe('ComponentName', () => {
  describe('when [condition]', () => {
    it('should [expected behavior]', () => {
      // test
    })
  })
})
```

### 2. Test Structure (AAA Pattern)
```typescript
it('should handle user login', () => {
  // Arrange
  const { getByLabelText, getByRole } = render(<LoginPage />)
  
  // Act
  fireEvent.change(getByLabelText('Username'), { target: { value: 'admin' } })
  fireEvent.click(getByRole('button', { name: /sign in/i }))
  
  // Assert
  expect(mockLogin).toHaveBeenCalledWith('admin', 'password')
})
```

### 3. Mocking Best Practices
- ✅ Mock external dependencies (API, WebSocket)
- ✅ Use MSW for API mocking when possible
- ✅ Mock React Router for page tests
- ✅ Mock Zustand stores when testing components
- ✅ Use test data factories for consistent test data

### 4. Coverage Goals per File Type
- **Utilities**: 90%+ (pure functions, easy to test)
- **Stores**: 80%+ (critical business logic)
- **Hooks**: 75%+ (complex state management)
- **UI Components**: 85%+ (user interactions)
- **Page Components**: 65%+ (integration, focus on critical paths)
- **Complex Components**: 60%+ (focus on main functionality)

---

## Timeline Estimate

| Phase | Duration | Coverage Target |
|-------|----------|----------------|
| Phase 1 | 1-2 weeks | 15-20% |
| Phase 2 | 2-3 weeks | 35-40% |
| Phase 3 | 2-3 weeks | 50-55% |
| Phase 4 | 3-4 weeks | 65-70% |
| Phase 5 | 2-3 weeks | 70%+ |
| **Total** | **10-15 weeks** | **70%+** |

*Note: Timeline assumes part-time work (10-15 hours/week)*

---

## Quick Wins (Start Here)

### Week 1 Quick Wins
1. ✅ `src/utils/statusMapping.ts` - Pure functions, easy to test (2 hours)
2. ✅ `src/components/ui/Button.tsx` - Simple component (1 hour)
3. ✅ `src/components/ui/Input.tsx` - Simple component (1 hour)
4. ✅ `src/components/ui/StatusBadge.tsx` - Simple component (1 hour)
5. ✅ `src/pages/NotFoundPage.tsx` - Simple page (30 minutes)

**Estimated Coverage Gain**: +5-7%

---

## Maintenance

### Continuous Improvement
- ✅ Run coverage reports before PRs
- ✅ Set minimum coverage thresholds in CI
- ✅ Review coverage reports weekly
- ✅ Add tests for bug fixes
- ✅ Refactor untestable code

### Coverage Thresholds (CI)
```json
{
  "statements": 70,
  "branches": 60,
  "functions": 65,
  "lines": 70
}
```

---

## Resources

### Testing Libraries
- **Vitest**: Test runner
- **@testing-library/react**: Component testing
- **@testing-library/user-event**: User interactions
- **@testing-library/jest-dom**: DOM matchers
- **MSW**: API mocking
- **vitest-mock-extended**: Advanced mocking

### Documentation
- [Vitest Documentation](https://vitest.dev/)
- [React Testing Library](https://testing-library.com/react)
- [Testing Best Practices](https://kentcdodds.com/blog/common-mistakes-with-react-testing-library)

---

## Notes

- Focus on **behavior** over implementation details
- Test **user interactions**, not internal state
- Use **integration tests** for complex flows
- **Mock external dependencies** (API, WebSocket)
- Keep tests **maintainable** and **readable**
- Write tests **before** fixing bugs (TDD when possible)

---

**Last Updated**: 2025-12-08
**Current Coverage**: 3.17%
**Target Coverage**: 70%+
**Status**: Planning Phase

