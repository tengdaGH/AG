import { test, expect } from '@playwright/test';

test.describe('TOEFL 2026 Rater Dashboard E2E', () => {
    test.beforeEach(async ({ page }) => {
        // Log in as Rater
        await page.goto('http://localhost:3000/login');
        const roleSelect = page.locator('select');
        await roleSelect.selectOption('RATER');
        await page.click('button[type="submit"]');
        await page.waitForURL(/.*\/dashboard\/rater/);
    });

    test('Rater can view the scoring queue', async ({ page }) => {
        // Assert header loads
        await expect(page.locator('h1')).toContainText('Rater Portal');

        // Assert Scoring Queue Section
        await expect(page.locator('text=Scoring Queue')).toBeVisible();
    });

    test('Rater can view assigned speaking and writing responses', async ({ page }) => {
        // Mock data validation
        await expect(page.locator('text=Speaking: Virtual Interview').first()).toBeVisible();
        await expect(page.locator('text=Writing: Write an Email').first()).toBeVisible();
        await expect(page.locator('text=Writing: Academic Discussion').first()).toBeVisible();

        // Ensure status indicators load
        await expect(page.locator('text=PENDING').first()).toBeVisible();
        await expect(page.locator('text=AI SCORED').first()).toBeVisible();
    });

    test('Rater can interact with the Score button', async ({ page }) => {
        const scoreButton = page.getByRole('button', { name: 'Score' }).first();
        await expect(scoreButton).toBeVisible();

        // Simulate dialogue prompt when button is clicked (Not fully hooked up to a modal in MVP yet)
        page.on('dialog', async dialog => {
            expect(dialog.message()).toContain('Open scoring rubric for Session');
            await dialog.accept();
        });

        await scoreButton.click();
    });
});
