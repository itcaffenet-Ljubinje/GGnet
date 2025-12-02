import { test as setup, expect } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

/**
 * Authentication Setup for E2E Tests
 * 
 * This file handles authentication state for all tests.
 * It logs in once and saves the authentication state to a file.
 */

const authFile = path.join(__dirname, '../.auth/user.json');

setup('authenticate', async ({ page }) => {
  // Navigate to login page
  await page.goto('/');
  
  // Wait for login form
  await page.waitForSelector('input[name="username"]', { timeout: 10000 });
  
  // Fill credentials
  await page.locator('input[name="username"]').fill('admin');
  await page.locator('input[name="password"]').fill('admin123');
  
  // Submit login
  await page.locator('button[type="submit"]').click();
  
  // Wait for successful login (redirect away from login page)
  await page.waitForURL(/\/dashboard|\/$/, { timeout: 10000 });
  
  // Verify we're logged in
  await expect(page.locator('input[name="username"]')).not.toBeVisible();
  
  // Save authentication state
  await page.context().storageState({ path: authFile });
  
  console.log('Authentication state saved to', authFile);
});

