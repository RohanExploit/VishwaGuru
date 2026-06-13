import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Grant permissions
        await page.context.grant_permissions(['geolocation'], origin='http://localhost:5173')
        await page.context.set_geolocation({'latitude': 19.0760, 'longitude': 72.8777}) # Mumbai

        print("Navigating to Report Form...")
        try:
            await page.goto("http://localhost:5173/report", timeout=10000)
        except Exception as e:
            print(f"Failed to load page: {e}")
            await browser.close()
            return

        # Wait for form
        await page.wait_for_timeout(1000)

        # Mock Location
        print("Clicking Location button...")
        # Button with 📍
        loc_btn = page.get_by_role("button", name="📍")
        if await loc_btn.is_visible():
             await loc_btn.click()
        else:
             print("Location button not found")

        await page.wait_for_timeout(1000) # Wait for location update

        # Check for Nearby Button
        nearby_btn = page.get_by_text("Check for existing reports nearby")
        if await nearby_btn.is_visible():
            print("SUCCESS: Nearby button is visible.")
        else:
            print("FAILURE: Nearby button not found. (Maybe location not set?)")
            await browser.close()
            return

        # Mock API response for nearby issues
        await page.route("**/api/issues/nearby*", lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body='[{"id": 1, "description": "Test Issue", "category": "pothole", "latitude": 19.076, "longitude": 72.877, "distance_meters": 10, "upvotes": 5, "created_at": "2023-01-01", "status": "open"}]'
        ))

        # Click Nearby Button
        print("Clicking Nearby button...")
        await nearby_btn.click()

        # Check Modal
        await page.wait_for_timeout(1000)
        modal_title = page.get_by_text("Nearby Issues (1)")
        if await modal_title.is_visible():
            print("SUCCESS: Nearby Issues modal opened.")
        else:
            print("FAILURE: Nearby Issues modal did not open.")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
