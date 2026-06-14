const { test, expect } = require('@playwright/test');

test('CameraCheckModal should render correctly', async ({ page }) => {
  await page.goto('http://localhost:5173/');
});
