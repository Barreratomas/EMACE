import { test, expect } from '@playwright/test';

test('Login flow', async ({ page }) => {
  // Mock login API
  await page.route('**/api/v1/auth/login', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        access_token: 'fake-token',
        refresh_token: 'fake-refresh',
        user: { id: '1', email: 'admin@emace.ai', name: 'Admin' }
      }),
    });
  });

  await page.goto('/auth/login');
  
  // Check if login form is visible
  await expect(page.getByText(/INICIAR_SESIÓN/i)).toBeVisible();
  
  // Fill form
  await page.fill('input[name="email"]', 'admin@emace.ai');
  await page.fill('input[name="password"]', 'password123');
  
  // Click submit
  await page.click('button[type="submit"]');
  
  // Should redirect to inventory (based on LoginForm logic)
  await expect(page).toHaveURL(/\/inventory/);
  await expect(page.getByText(/INVENTARIO_CENTRAL/i)).toBeVisible();
});
