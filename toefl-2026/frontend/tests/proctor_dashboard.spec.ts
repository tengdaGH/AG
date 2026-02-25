import { test, expect } from '@playwright/test';

test.describe('TOEFL 2026 Proctor Dashboard E2E', () => {
    test.beforeEach(async ({ page }) => {
        // Log in as Proctor
        await page.goto('http://localhost:3000/login');
        const roleSelect = page.locator('select');
        await roleSelect.selectOption('PROCTOR');
        await page.click('button[type="submit"]');
        await page.waitForURL(/.*\/dashboard\/proctor/);
    });

    test('Proctor can view active test sessions and station monitors', async ({ page }) => {
        // Assert header loads
        await expect(page.locator('h1')).toContainText('Proctor Portal');

        // Ensure "Active Session" header works
        await expect(page.locator('text=Active Session ID')).toBeVisible();

        // Ensure "Live Monitoring" component is rendering
        await expect(page.locator('text=Test Center - Live Monitoring')).toBeVisible();
    });

    test('Proctor can monitor active stations', async ({ page }) => {
        // Verify mock stations are showing
        await expect(page.locator('text=Station 04 - John Doe')).toBeVisible();
        await expect(page.locator('text=Station 12 - Jane Smith')).toBeVisible();
        await expect(page.locator('text=Station 15 - Empty')).toBeVisible();

        // Assert the Station status text is correctly mapped from i18n
        await expect(page.locator('text=IN PROGRESS').first()).toBeVisible();
    });

    test('Proctor can Lockdown all stations', async ({ page }) => {
        // Find the lockdown button (mapped from i18n "Lockdown All Stations")
        const lockdownButton = page.getByRole('button', { name: 'Lockdown All Stations' });
        await expect(lockdownButton).toBeVisible();

        // Simulate click and confirm the browser's native confirm alert
        page.on('dialog', async dialog => {
            expect(dialog.message()).toContain('Lockdown procedure initiated for all stations');
            await dialog.accept();
        });

        await lockdownButton.click();
    });
});
