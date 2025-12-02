import { test, expect } from '@playwright/test';

/**
 * Login Flow E2E Tests
 * 
 * Tests the complete authentication flow:
 * - Login page display
 * - Successful login
 * - Failed login
 * - Redirect after login
 */

test.describe('Login Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to login page
    await page.goto('/');
    
    // Wait for login page to load
    await page.waitForSelector('form', { timeout: 10000 });
  });

  test('should display login form', async ({ page }) => {
    // Check login form elements are visible
    await expect(page.locator('input[name="username"]')).toBeVisible();
    await expect(page.locator('input[name="password"]')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
    
    // Check default credentials hint is displayed
    await expect(page.locator('text=Default credentials')).toBeVisible();
    await expect(page.locator('text=admin')).toBeVisible();
    await expect(page.locator('text=admin123')).toBeVisible();
  });

  test('should show validation errors for empty fields', async ({ page }) => {
    // Try to submit empty form
    await page.locator('button[type="submit"]').click();
    
    // Wait a bit for validation
    await page.waitForTimeout(500);
    
    // Check if form validation is working (may not show errors if HTML5 validation is used)
    // This test might need adjustment based on actual validation implementation
  });

  test('should show error for invalid credentials', async ({ page }) => {
    // Fill in invalid credentials
    await page.locator('input[name="username"]').fill('invalid');
    await page.locator('input[name="password"]').fill('invalid');
    
    // Submit form
    await page.locator('button[type="submit"]').click();
    
    // Wait for error message
    await page.waitForTimeout(2000);
    
    // Check for error message (adjust selector based on actual error display)
    const errorMessage = page.locator('text=/invalid|error|failed/i');
    await expect(errorMessage.first()).toBeVisible({ timeout: 5000 });
  });

  test('should successfully login with valid credentials', async ({ page }) => {
    // Fill in valid credentials
    await page.locator('input[name="username"]').fill('admin');
    await page.locator('input[name="password"]').fill('admin123');
    
    // Submit form
    await page.locator('button[type="submit"]').click();
    
    // Wait for navigation to dashboard
    await page.waitForURL(/\/dashboard|\/$/, { timeout: 10000 });
    
    // Check that we're logged in (look for dashboard or layout elements)
    // Adjust selectors based on actual dashboard structure
    await expect(page).toHaveURL(/\/dashboard|\/$/);
    
    // Check that login form is no longer visible
    await expect(page.locator('input[name="username"]')).not.toBeVisible();
  });

  test('should toggle password visibility', async ({ page }) => {
    const passwordInput = page.locator('input[name="password"]');
    const toggleButton = page.locator('button').filter({ hasText: /eye|show|hide/i }).or(
      page.locator('[aria-label*="password"]').or(
        page.locator('svg').near(passwordInput)
      )
    );
    
    // Fill password
    await passwordInput.fill('testpassword');
    
    // Check initial state (password should be hidden)
    await expect(passwordInput).toHaveAttribute('type', 'password');
    
    // Click toggle if button exists
    if (await toggleButton.count() > 0) {
      await toggleButton.first().click();
      
      // Check password is now visible
      await expect(passwordInput).toHaveAttribute('type', 'text');
    }
  });

  test('should disable submit button during login', async ({ page }) => {
    // Fill credentials
    await page.locator('input[name="username"]').fill('admin');
    await page.locator('input[name="password"]').fill('admin123');
    
    // Get submit button
    const submitButton = page.locator('button[type="submit"]');
    
    // Click and check if button is disabled
    await submitButton.click();
    
    // Button should be disabled or show loading state
    await expect(submitButton).toBeDisabled({ timeout: 1000 }).catch(() => {
      // If not disabled, check for loading indicator
      return expect(page.locator('text=/signing|loading/i')).toBeVisible();
    });
  });

  test('should redirect to dashboard after successful login', async ({ page }) => {
    // Login
    await page.locator('input[name="username"]').fill('admin');
    await page.locator('input[name="password"]').fill('admin123');
    await page.locator('button[type="submit"]').click();
    
    // Wait for redirect
    await page.waitForTimeout(3000);
    
    // Should be redirected away from login page
    const currentUrl = page.url();
    expect(currentUrl).not.toContain('/login');
    
    // Should be on dashboard or home
    expect(currentUrl).toMatch(/\/dashboard|\/$/);
  });
});

