# E2E Testing with Playwright

End-to-end tests for GGnet frontend using Playwright.

## Setup

### Install Dependencies

```bash
cd frontend
npm install
```

### Install Playwright Browsers

```bash
npx playwright install
```

## Running Tests

### Run All E2E Tests

```bash
npm run test:e2e
```

### Run Tests in UI Mode

```bash
npm run test:e2e:ui
```

### Run Tests in Headed Mode (see browser)

```bash
npm run test:e2e:headed
```

### Debug Tests

```bash
npm run test:e2e:debug
```

### View Test Report

```bash
npm run test:e2e:report
```

## Test Structure

```
e2e/
├── login.spec.ts          # Login flow tests
├── dashboard.spec.ts      # Dashboard tests
├── machines.spec.ts       # Machines page tests
└── setup/
    └── auth.setup.ts      # Authentication setup
```

## Writing Tests

### Basic Test Structure

```typescript
import { test, expect } from '@playwright/test';

test('should do something', async ({ page }) => {
  await page.goto('/');
  await expect(page.locator('h1')).toContainText('Welcome');
});
```

### Using Authenticated State

Tests automatically use authenticated state from `setup/auth.setup.ts`:

```typescript
test.use({ storageState: 'e2e/.auth/user.json' });

test('authenticated test', async ({ page }) => {
  // Already logged in
  await page.goto('/dashboard');
});
```

## Configuration

See `playwright.config.ts` for:
- Base URL configuration
- Browser selection
- Test timeouts
- Screenshot/video settings
- Web server setup

## Test Data

Default test credentials:
- Username: `admin`
- Password: `admin123`

⚠️ **Note:** These are for testing only. Change in production!

## CI/CD Integration

Tests can be run in CI/CD pipelines:

```yaml
# GitHub Actions example
- name: Install Playwright
  run: npx playwright install --with-deps

- name: Run E2E tests
  run: npm run test:e2e
```

## Debugging

1. **Use UI Mode:** `npm run test:e2e:ui`
2. **Use Debug Mode:** `npm run test:e2e:debug`
3. **Check Screenshots:** Failed tests save screenshots in `test-results/`
4. **Check Videos:** Failed tests save videos in `test-results/`
5. **Check Traces:** Run with `--trace on` to generate traces

## Best Practices

1. **Use data-testid attributes** in components for stable selectors
2. **Wait for elements** before interacting
3. **Use page object pattern** for complex pages
4. **Keep tests independent** - don't rely on test order
5. **Clean up after tests** if needed

## Troubleshooting

### Tests fail with timeout
- Check if frontend/backend servers are running
- Increase timeout in `playwright.config.ts`
- Check network connectivity

### Tests fail to authenticate
- Ensure admin user exists in test database
- Check backend API is accessible
- Review authentication setup in `setup/auth.setup.ts`

### Flaky tests
- Add explicit waits
- Use `waitFor` instead of `waitForTimeout`
- Check for race conditions

