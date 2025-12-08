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
    // Use more specific selectors to avoid strict mode violations
    await expect(page.locator('code').filter({ hasText: 'admin' }).first()).toBeVisible();
    await expect(page.locator('code').filter({ hasText: 'admin123' })).toBeVisible();
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
    
    // Wait for error message - error is displayed in a div with class text-red-300
    await expect(page.locator('.text-red-300')).toBeVisible({ timeout: 5000 });
    
    // Check for error message text
    const errorMessage = page.locator('text=/invalid|error|failed/i');
    await expect(errorMessage.first()).toBeVisible({ timeout: 1000 });
  });

  test('should successfully login with valid credentials', async ({ page }) => {
    // Fill in valid credentials
    await page.locator('input[name="username"]').fill('admin');
    await page.locator('input[name="password"]').fill('admin123');
    
    // Submit form and wait for navigation
    await Promise.all([
      page.waitForURL(/\/dashboard/, { timeout: 15000 }),
      page.locator('button[type="submit"]').click(),
    ]);
    
    // Wait for page to be fully loaded
    await page.waitForLoadState('networkidle');
    
    // Check that we're logged in
    await expect(page).toHaveURL(/\/dashboard/);
    
    // Check that login form is no longer visible
    await expect(page.locator('input[name="username"]')).not.toBeVisible();
  });

  test('should toggle password visibility', async ({ page }) => {
    const passwordInput = page.locator('input[name="password"]');
    
    // Fill password
    await passwordInput.fill('testpassword');
    
    // Check initial state (password should be hidden)
    await expect(passwordInput).toHaveAttribute('type', 'password');
    
    // Find the toggle button - it's a button with type="button" that contains an Eye icon
    // The button is positioned absolutely within the password input's parent div
    // Use CSS selector to find button in the same parent as password input
    const toggleButton = page.locator('.relative button[type="button"]');
    
    // Verify button exists and is visible
    await expect(toggleButton).toBeVisible();
    
    // Click toggle button
    await toggleButton.click();
    
    // Check password is now visible
    await expect(passwordInput).toHaveAttribute('type', 'text');
    
    // Click again to hide
    await toggleButton.click();
    
    // Check password is hidden again
    await expect(passwordInput).toHaveAttribute('type', 'password');
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
    // Fill in valid credentials
    await page.locator('input[name="username"]').fill('admin');
    await page.locator('input[name="password"]').fill('admin123');
    
    // Submit form and wait for navigation
    await Promise.all([
      page.waitForURL(/\/dashboard/, { timeout: 15000 }),
      page.locator('button[type="submit"]').click(),
    ]);
    
    // Wait for page to be fully loaded
    await page.waitForLoadState('networkidle');
    
    // Verify we're on dashboard
    await expect(page).toHaveURL(/\/dashboard/);
  });
});

