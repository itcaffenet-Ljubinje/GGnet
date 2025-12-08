# Test Coverage Quick Start Guide

## Getting Started

This guide will help you quickly start adding tests to improve coverage.

## Prerequisites

All testing dependencies are already installed:
- ✅ `vitest` - Test runner
- ✅ `@testing-library/react` - Component testing
- ✅ `@testing-library/user-event` - User interactions
- ✅ `@testing-library/jest-dom` - DOM matchers

## Quick Start

### 1. Use the Test Utilities

Import the custom render function from test utilities:

```typescript
import { render, screen } from '../__tests__/setup/test-utils'
import userEvent from '@testing-library/user-event'
```

### 2. Use Mock Data Factories

Import mock data factories:

```typescript
import { createMockUser, createMockMachine } from '../__tests__/setup/mocks'
```

### 3. Write Your First Test

```typescript
import { describe, it, expect } from 'vitest'
import { render, screen } from '../__tests__/setup/test-utils'
import { Button } from './Button'

describe('Button', () => {
  it('should render button with text', () => {
    render(<Button>Click me</Button>)
    expect(screen.getByRole('button', { name: /click me/i })).toBeInTheDocument()
  })
})
```

## Example Test Files

See `src/components/ui/Button.test.tsx.example` for a complete example.

## Test Structure

Follow the AAA pattern (Arrange, Act, Assert):

```typescript
it('should handle user interaction', () => {
  // Arrange
  const { getByRole } = render(<MyComponent />)
  
  // Act
  fireEvent.click(getByRole('button'))
  
  // Assert
  expect(someFunction).toHaveBeenCalled()
})
```

## Running Tests

```bash
# Run all tests
npm run test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage

# Run tests in UI mode
npm run test:ui
```

## Priority Order

Start with these files for quick wins:

1. ✅ `src/utils/statusMapping.ts` - Pure functions (2 hours)
2. ✅ `src/components/ui/Button.tsx` - Simple component (1 hour)
3. ✅ `src/components/ui/Input.tsx` - Simple component (1 hour)
4. ✅ `src/components/ui/StatusBadge.tsx` - Simple component (1 hour)
5. ✅ `src/pages/NotFoundPage.tsx` - Simple page (30 minutes)

## Best Practices

1. **Test behavior, not implementation**
   ```typescript
   // ❌ Bad - tests implementation
   expect(component.state.isOpen).toBe(true)
   
   // ✅ Good - tests behavior
   expect(screen.getByRole('dialog')).toBeVisible()
   ```

2. **Use semantic queries**
   ```typescript
   // ❌ Bad
   screen.getByTestId('submit-button')
   
   // ✅ Good
   screen.getByRole('button', { name: /submit/i })
   ```

3. **Mock external dependencies**
   ```typescript
   import { vi } from 'vitest'
   
   const mockApiCall = vi.fn()
   vi.mock('../lib/api', () => ({
     api: {
       get: mockApiCall
     }
   }))
   ```

4. **Test user interactions**
   ```typescript
   import userEvent from '@testing-library/user-event'
   
   const user = userEvent.setup()
   await user.click(screen.getByRole('button'))
   ```

## Coverage Goals

- **Utilities**: 90%+ (pure functions)
- **Stores**: 80%+ (business logic)
- **Hooks**: 75%+ (state management)
- **UI Components**: 85%+ (user interactions)
- **Pages**: 65%+ (integration)

## Need Help?

- See `TEST_COVERAGE_PLAN.md` for the complete plan
- Check `src/components/ui/Button.test.tsx.example` for examples
- Review existing test: `src/App.test.tsx`

## Next Steps

1. Pick a file from Phase 1 of the plan
2. Write tests following the examples
3. Run coverage to see improvement
4. Continue with next priority file

Happy Testing! 🧪

