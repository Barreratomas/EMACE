import { test, expect } from '@playwright/test';

test('Home renders hero', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'EMACE' })).toBeVisible();
});
