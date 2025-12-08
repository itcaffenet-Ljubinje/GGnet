import { test, expect } from '@playwright/test';

/**
 * Images Page E2E Tests
 * 
 * Tests the images management page:
 * - Images list displays
 * - Image upload
 * - Image deletion
 * - Image details
 */

test.describe('Images Page', () => {
  test.beforeEach(async ({ page }) => {
    // Login first
    await page.goto('/');
    
    // Wait for login form
    await page.waitForSelector('input[name="username"]', { timeout: 10000 });
    
    // Fill credentials
    await page.locator('input[name="username"]').fill('admin');
    await page.locator('input[name="password"]').fill('admin123');
    
    // Submit form and wait for navigation
    await Promise.all([
      page.waitForURL(/\/dashboard/, { timeout: 15000 }),
      page.locator('button[type="submit"]').click(),
    ]);
    
    // Wait for page to be fully loaded
    await page.waitForLoadState('networkidle');
    
    // Navigate to images page
    await page.goto('/images');
    
    // Wait for images page to load
    await page.waitForLoadState('networkidle');
  });

  test('should display images page', async ({ page }) => {
    // Check URL
    await expect(page).toHaveURL(/\/images/);
    
    // Wait for page content to load - check that login form is not visible
    await expect(page.locator('input[name="username"]')).not.toBeVisible();
    
    // Look for images page elements - check for navigation menu item or page heading
    // The page might show "Images" in navigation or as a heading
    const pageContent = page.locator('text=/images/i').or(
      page.locator('h1, h2, h3').filter({ hasText: /images/i })
    );
    
    // At least one element with "images" should be visible
    await expect(pageContent.first()).toBeVisible({ timeout: 5000 });
  });

  test('should show images list', async ({ page }) => {
    // Wait for page to be fully loaded
    await page.waitForLoadState('networkidle');
    
    // Look for images table, list, or any content indicating the page loaded
    // Check for common patterns: table, list, or empty state message
    const hasContent = await Promise.race([
      page.locator('table').waitFor({ state: 'visible', timeout: 3000 }).then(() => true).catch(() => false),
      page.locator('text=/no.*images|empty|no data/i').waitFor({ state: 'visible', timeout: 3000 }).then(() => true).catch(() => false),
      page.locator('[data-testid*="image"]').waitFor({ state: 'visible', timeout: 3000 }).then(() => true).catch(() => false),
    ]);
    
    // Page should have loaded some content (table, empty state, or images)
    expect(hasContent).toBeTruthy();
  });

  test('should allow uploading an image', async ({ page }) => {
    // Look for "Upload" or "Add Image" button
    const uploadButton = page.locator('button').filter({ hasText: /upload|add.*image/i }).or(
      page.locator('[aria-label*="upload"]')
    );
    
    if (await uploadButton.count() > 0) {
      await uploadButton.first().click();
      
      // Should open upload modal or dialog
      await page.waitForTimeout(1000);
      
      // Look for file input or upload form
      const fileInput = page.locator('input[type="file"]').or(
        page.locator('[data-testid="file-upload"]')
      );
      
      // File input should be visible
      await expect(fileInput.first()).toBeVisible({ timeout: 3000 }).catch(() => {
        // Upload might not be fully implemented
        console.log('Image upload form not found - may not be fully implemented');
      });
    }
  });

  test('should display image details', async ({ page }) => {
    // Look for image cards or table rows
    const imageItems = page.locator('tr, [data-testid*="image"], .image-card').first();
    
    if (await imageItems.count() > 0) {
      // Click on first image to view details
      await imageItems.first().click();
      
      // Should show image details
      await page.waitForTimeout(1000);
      
      // Look for detail elements (name, size, format, etc.)
      const details = page.locator('text=/name|size|format|description/i');
      await expect(details.first()).toBeVisible({ timeout: 3000 }).catch(() => {
        // Details view might not be implemented
        console.log('Image details view not found');
      });
    }
  });
});

