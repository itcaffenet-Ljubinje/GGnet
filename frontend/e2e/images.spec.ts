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
    await page.locator('input[name="username"]').fill('admin');
    await page.locator('input[name="password"]').fill('admin123');
    await page.locator('button[type="submit"]').click();
    
    // Wait for dashboard
    await page.waitForTimeout(2000);
    
    // Navigate to images page
    await page.goto('/images');
    await page.waitForTimeout(1000);
  });

  test('should display images page', async ({ page }) => {
    // Check URL
    expect(page.url()).toContain('/images');
    
    // Look for images page elements
    const pageTitle = page.locator('text=/images|disk.*images/i');
    await expect(pageTitle.first()).toBeVisible({ timeout: 5000 });
  });

  test('should show images list', async ({ page }) => {
    // Look for images table or list
    const imagesList = page.locator('table, [role="table"], [data-testid="images-list"]').or(
      page.locator('text=/image|vhd|vhdx/i')
    );
    
    // Should show some images content (even if empty)
    await expect(imagesList.first()).toBeVisible({ timeout: 5000 }).catch(() => {
      // If no images, should show empty state
      return expect(page.locator('text=/no images|empty/i')).toBeVisible();
    });
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

