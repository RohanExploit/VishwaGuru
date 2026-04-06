const { test, expect } = require('@playwright/test');

test('CameraCheckModal opens and displays status', async ({ page }) => {
  // Mock API routes to prevent ECONNREFUSED
  await page.route('**/api/responsibility-map', route => route.fulfill({ status: 200, json: {} }));
  await page.route('**/api/issues/recent*', route => route.fulfill({ status: 200, json: [] }));
  await page.route('**/api/stats', route => route.fulfill({ status: 200, json: {} }));
  await page.route('**/api/auth/me', route => route.fulfill({ status: 200, json: { id: 1, email: 'test@example.com', role: 'user' } }));

  // Go to page
  await page.goto('http://localhost:5173/');

  // Inject token to bypass auth
  await page.evaluate(() => {
    localStorage.setItem('token', 'fake-token');
  });

  // Reload to apply auth state
  await page.reload();

  await page.waitForLoadState('networkidle');

  // Find the diagnostics hub element
  await page.evaluate(() => {
    const elements = document.querySelectorAll('*');
    for (let el of elements) {
      if (el.textContent === 'Diagnostics Hub' || el.textContent === 'Camera Check') {
          let btn = el;
          while (btn && btn.tagName !== 'BUTTON') {
             btn = btn.parentElement;
          }
          if (btn) {
              btn.click();
              break;
          }
      }
    }
  });

  // Verify the modal appears
  const modalHeader = page.locator('h3', { hasText: 'Camera Diagnostics' });
  await expect(modalHeader).toBeVisible({ timeout: 10000 });

  // Wait for the camera permission to either fail or succeed (typically fails in headless)
  const statusContainer = page.locator('.bg-gray-100');
  await expect(statusContainer).toBeVisible();

  // Close the modal
  const closeButton = page.locator('button', { hasText: 'Close' });
  await closeButton.click();

  // Verify it closed
  await expect(modalHeader).not.toBeVisible();
});
