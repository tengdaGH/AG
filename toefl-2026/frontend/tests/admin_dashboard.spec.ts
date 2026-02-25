import { test, expect } from '@playwright/test';

test.describe('TOEFL 2026 Admin Dashboard E2E', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('http://localhost:3000/login');
        const roleSelect = page.locator('select');
        await roleSelect.selectOption('ADMIN');
        await page.click('button[type="submit"]');
        await page.waitForURL(/.*\/dashboard\/admin/);
    });

    test('Admin can view the platform overview stats', async ({ page }) => {
        await expect(page.locator('h1')).toContainText('Admin Portal');
        await expect(page.locator('text=Platform Overview')).toBeVisible();
        await expect(page.locator('text=Active Test Sessions')).toBeVisible();
    });

    test('Admin can navigate to the Item Bank Management tool', async ({ page }) => {
        // Find the button inside the Item Bank Management card
        const launchItemBankButton = page.getByRole('button', { name: 'Launch Item Bank Designer' });
        await expect(launchItemBankButton).toBeVisible();

        // It should route to /dashboard/admin/items
        await launchItemBankButton.click();
        await page.waitForURL(/.*\/dashboard\/admin\/items/);

        // Verify we are in the Item Bank Management List
        await expect(page.locator('text=Item Bank Management')).toBeVisible();

        // Navigate to the Item Bank Designer
        const createItemButton = page.getByRole('button', { name: '+ Create New Item' });
        await expect(createItemButton).toBeVisible();
        await createItemButton.click();

        await page.waitForURL(/.*\/dashboard\/admin\/items\/create/);
        await expect(page.locator('text=Item Bank Designer').first()).toBeVisible();
    });

    test('Admin can log out safely', async ({ page }) => {
        const signOutButton = page.getByRole('button', { name: 'Sign Out' });
        await signOutButton.click();

        await page.waitForURL(/.*\/login/);
        await expect(page.locator('text=Sign In')).toBeVisible();
    });
});
