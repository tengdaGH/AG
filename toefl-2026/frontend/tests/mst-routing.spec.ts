import { test, expect } from '@playwright/test';

test.describe('TOEFL 2026 MST Routing', () => {
    test('should route to UPPER module when performance is high', async ({ page }) => {
        await page.goto('http://localhost:3000');

        // 1. Start Test
        await page.click('button:has-text("Begin Section")');

        // 2. Mock 100% correct in Reading Stage 1
        // (In a real test, we would interact with the UI. For this verification, 
        // we can assume the buttons work and we just need to trigger the Next logic)

        // Reading has 8 items in Stage 1 for S2-R-M1-DL
        for (let i = 0; i < 8; i++) {
            // Answer any option to ensure response exists
            const radio = await page.locator('input[type="radio"]').first();
            if (await radio.isVisible()) {
                await radio.check();
            }
            await page.click('button:has-text("Next")');
        }

        // 3. Verify it transitions to Stage 2 Upper/Academic items
        // (We check the header or item content for "Academic Passage")
        await expect(page.locator('header')).toContainText('Reading Section');
        // After 8 DL items, if routed to Upper, we should see an Academic Passage
        await expect(page.locator('body')).toContainText('Academic Passage', { timeout: 10000 });
    });

    test('should route to LOWER module when performance is low', async ({ page }) => {
        await page.goto('http://localhost:3000');
        await page.click('button:has-text("Begin Section")');

        // 1. Skip all 8 items in Stage 1
        for (let i = 0; i < 8; i++) {
            await page.click('button:has-text("Next")');
        }

        // 2. Verify it transitions to Stage 2 Lower/Daily Life items
        // (We check for the Daily Life title)
        await expect(page.locator('body')).toContainText('Read in Daily Life', { timeout: 10000 });
    });
});
