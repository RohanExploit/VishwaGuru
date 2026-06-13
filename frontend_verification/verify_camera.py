import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        # Use fake device for media stream to simulate camera in headless mode
        browser = await p.chromium.launch(headless=True, args=['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream'])
        page = await browser.new_page()

        # Grant camera permissions
        await page.context.grant_permissions(['camera'], origin='http://localhost:5173')

        page.on("console", lambda msg: print(f"CONSOLE: {msg.text}"))
        page.on("pageerror", lambda exc: print(f"PAGE ERROR: {exc}"))

        print("Navigating to Home...")
        try:
             await page.goto("http://localhost:5173/home", timeout=10000)
        except Exception as e:
             print(f"Failed to load home: {e}")
             await browser.close()
             return

        print("Clicking Camera Check...")
        try:
            await page.get_by_text("Camera Check").click()
        except Exception:
            print("Camera Check button not found")
            await browser.close()
            return

        await page.wait_for_timeout(2000)

        # Check Modal
        if await page.get_by_text("Camera Diagnostics").is_visible():
            print("Camera Diagnostics Modal opened.")
        else:
            print("FAILURE: Modal not found.")
            await browser.close()
            return

        # Check Video
        video = page.locator("video")
        if await video.is_visible():
            print("SUCCESS: Video element is visible.")
            # Check if srcObject is set (requires eval)
            # We wait a bit for the stream to start
            await page.wait_for_timeout(1000)

            try:
                # Check if srcObject is present (it's not an attribute, it's a property)
                has_src_object = await video.evaluate("el => el.srcObject !== null")
                if has_src_object:
                    print("SUCCESS: Video has srcObject (stream attached).")
                else:
                    print("WARNING: Video element found but srcObject is null.")

                # Check readyState
                ready_state = await video.evaluate("el => el.readyState")
                print(f"Video readyState: {ready_state}")

            except Exception as e:
                print(f"Error evaluating video: {e}")

        else:
            print("FAILURE: Video element not found.")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
