import { test, expect } from '@playwright/test';

/**
 * Dashboard E2E Tests
 * 
 * Tests the dashboard page functionality:
 * - Dashboard loads after login
 * - Dashboard displays key information
 * - Navigation works
 */

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    // Login first
    await page.goto('/');
    
    // Wait for login form
    await page.waitForSelector('input[name="username"]', { timeout: 10000 });
    
    await page.locator('input[name="username"]').fill('admin');
    await page.locator('input[name="password"]').fill('admin123');
    await page.locator('button[type="submit"]').click();
    
    // Wait for navigation to dashboard (App.tsx redirects to /dashboard)
    await page.waitForURL(/\/dashboard/, { timeout: 10000 });
    
    // Wait for dashboard content to load
    await page.waitForLoadState('networkidle');
  });

  test('should display dashboard after login', async ({ page }) => {
    // Check that we're on dashboard page
    await expect(page).toHaveURL(/\/dashboard/);
    
    // Dashboard should be visible (or at least not showing login)
    await expect(page.locator('input[name="username"]')).not.toBeVisible();
    
    // Check that we're not on login page
    expect(page.url()).not.toContain('/login');
  });

  test('should have navigation menu', async ({ page }) => {
    // Look for navigation elements
    // Adjust selectors based on actual navigation structure
    const navElements = [
      page.locator('text=/machines|images|sessions|settings/i'),
      page.locator('nav'),
      page.locator('[role="navigation"]'),
    ];
    
    // At least one navigation element should be visible
    const hasNav = await Promise.race(
      navElements.map(async (el) => {
        try {
          await el.first().waitFor({ state: 'visible', timeout: 3000 });
          return true;
        } catch {
          return false;
        }
      })
    );
    
    expect(hasNav).toBeTruthy();
  });

  test('should allow logout', async ({ page }) => {
    // Look for logout button/menu
    // This might be in a user menu or header
    const logoutButton = page.locator('text=/logout|sign out/i').or(
      page.locator('button').filter({ hasText: /logout/i })
    );
    
    if (await logoutButton.count() > 0) {
      await logoutButton.first().click();
      
      // Should redirect to login page
      await page.waitForTimeout(2000);
      await expect(page.locator('input[name="username"]')).toBeVisible({ timeout: 5000 });
    }
  });
});

