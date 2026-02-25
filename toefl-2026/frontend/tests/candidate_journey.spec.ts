import { test, expect } from '@playwright/test';

test.describe('TOEFL 2026 Candidate Journey E2E', () => {

    test('Student can login, navigate the dashboard, and launch a test session', async ({ page }) => {
        // 1. Navigate to Login
        await page.goto('http://localhost:3000/login');

        // Expect a title "to contain" a substring.
        await expect(page).toHaveTitle(/TOEFL 2026/);

        // Ensure the role selector is present and can be interacted with
        const roleSelect = page.locator('select');
        await expect(roleSelect).toBeVisible();
        await roleSelect.selectOption('STUDENT');

        // Ensure React state updates
        await page.waitForTimeout(500);

        // Simulate clicking the Next/Login button to enter the dashboard
        await page.click('button[type="submit"]');

        // 2. Validate routing to Student Dashboard
        await expect(page).toHaveURL(/.*\/dashboard\/student/);
        await expect(page.locator('h1')).toContainText('My Assessments');

        // 3. Launch Demo Test Session
        // Find the launch button for the simulation
        const launchButton = page.getByRole('button', { name: 'Launch Proctor Check-in' });
        await expect(launchButton).toBeVisible();

        // We mock the window.location.href navigation in playwright by waiting for URL change
        await launchButton.click();
        await page.waitForURL(/.*\/test-session\/demo/);

        // 4. Validate Reading Section UI loads
        await expect(page.locator('text=Reading Section')).toBeVisible();
        await expect(page.locator('text=The Evolution of Artificial Coral Reefs')).toBeVisible();

        // 5. Interact with Reading Section and move to Listening
        // Select answers and click next
        await page.locator('input[value="A"]').first().click();
        await page.getByRole('button', { name: 'Next' }).click();

        await page.locator('input[value="B"]').first().click();
        await page.getByRole('button', { name: 'Next' }).click();

        await page.locator('input[value="C"]').first().click();

        // Accept the alert dialog that pops up when transitioning sections
        page.on('dialog', async dialog => {
            expect(dialog.message()).toContain('Reading Section completed');
            await dialog.accept();
        });

        await page.getByRole('button', { name: 'Submit Section' }).click();

        // 6. Validate transition to Listening Section
        await page.waitForURL(/.*\/test-session\/demo\/listening/);
        await expect(page.locator('text=Listening Section - Stage 1')).toBeVisible();

        // 7. Interact with Listening Section and move to Speaking
        // Click Begin Lecture
        await page.getByRole('button', { name: 'Begin Lecture' }).click();

        // Wait for audio playback to finish (it's accelerated in demo)
        await page.waitForSelector('text=Answering Time', { timeout: 15000 });

        // Answer 1 question since the demo block setup is 1
        await page.getByRole('button', { name: 'Submit & Enter Stage 2 Next Block' }).click();

        // Accept the Listening complete dialog
        page.on('dialog', async dialog => {
            expect(dialog.message()).toContain('Block 1 completed');
            await dialog.accept();
        });

        // 8. Validate transition to Speaking Section
        await page.waitForURL(/.*\/test-session\/demo\/speaking/);
        await expect(page.locator('text=Speaking Section: Virtual Interview')).toBeVisible();

        // 9. Interact with Speaking Section
        await page.getByRole('button', { name: 'Start Task' }).click();

        // Wait for Preparation timer (15s) and Recording timer (45s) to finish
        // We'll wait for the "Complete Test" button to become visible (it enables after recording)
        await page.waitForSelector('text=Complete Test', { timeout: 65000 });

        // Accept the Speaking scoring alert
        page.on('dialog', async dialog => {
            expect(dialog.message()).toContain('Speaking section completed');
            await dialog.accept();
        });

        // Navigate to the next section (Currently it routes to dashboard, let's update it in UI to route to writing later, or test writing separately, but for now we follow current flow)
        await page.getByRole('button', { name: 'Complete Test' }).click();

        // Check router redirect to writing section
        await page.waitForURL(/.*\/test-session\/demo\/writing/);
    });

    test('Student can complete the Writing Section Demo independently', async ({ page }) => {
        // Direct jump to writing test to test it in isolation
        await page.goto('http://localhost:3000/test-session/demo/writing');
        await expect(page.locator('text=Writing Section: Write an Email')).toBeVisible();

        // Type a ~50 word response
        const editor = page.locator('textarea');
        const mockResponse = "Dear Professor Miller, I am writing to inform you of a scheduling conflict... ".repeat(10);
        await editor.fill(mockResponse);

        // Accept the Writing scoring alert
        page.on('dialog', async dialog => {
            expect(dialog.message()).toContain('Email submitted & Graded by AI');
            await dialog.accept();
        });

        // Submit the essay
        await page.getByRole('button', { name: 'Submit Response' }).click();

        // Writing routes to student dashboard by default
        await page.waitForURL(/.*\/dashboard\/student/);
    });
});
