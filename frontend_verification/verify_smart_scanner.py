from playwright.sync_api import sync_playwright, expect
import os

def run_test():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream"]
        )
        context = browser.new_context(
            permissions=["camera"],
            viewport={"width": 375, "height": 812} # Mobile view
        )
        page = context.new_page()

        # Mock API calls
        page.route("**/api/issues/recent", lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body='[]'
        ))

        page.route("**/api/responsibility-map", lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body='{}'
        ))

        # Mock Smart Scan endpoint
        page.route("**/api/detect-smart-scan", lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body='{"label": "pothole", "score": 0.95}'
        ))

        try:
            # 1. Go to Home
            print("Navigating to Home...")
            page.goto("http://localhost:5173")

            # Wait for any of the main content to appear
            page.wait_for_selector("text=VishwaGuru", timeout=10000)

            # 2. Verify Impact Widget
            print("Verifying Impact Widget...")
            expect(page.get_by_text("Community Impact")).to_be_visible()
            expect(page.get_by_text("1240")).to_be_visible()

            # 3. Verify Smart Scanner Button
            print("Verifying Smart Scanner Button...")
            # Note: locator might need to be specific if text is split
            scanner_btn = page.locator("button").filter(has_text="Smart City Scanner")
            expect(scanner_btn).to_be_visible()

            # Take screenshot of Home
            os.makedirs("/home/jules/verification", exist_ok=True)
            page.screenshot(path="/home/jules/verification/home_screen.png")

            # 4. Click Button
            print("Clicking Smart Scanner...")
            scanner_btn.click()

            # 5. Verify Smart Scanner Page
            print("Verifying Smart Scanner Page...")
            expect(page.get_by_role("heading", name="Smart City Scanner")).to_be_visible()

            # Verify Start Button
            expect(page.get_by_role("button", name="Start Live Scan")).to_be_visible()

            # 6. Click Start
            print("Starting Scan...")
            page.get_by_role("button", name="Start Live Scan").click()

            # Wait for detection overlay (mocked response)
            # The component polls every 2 seconds.
            # We need to wait for the interval.
            print("Waiting for detection...")
            page.wait_for_timeout(3000)

            expect(page.get_by_text("pothole")).to_be_visible()
            expect(page.get_by_text("95% Confidence")).to_be_visible()

            # Take screenshot of Scanner
            page.screenshot(path="/home/jules/verification/smart_scanner.png")

            # 7. Click Report
            print("Clicking Report...")
            page.get_by_role("button", name="Report").click()

            # 8. Verify Report Form Pre-filled
            print("Verifying Report Form...")
            expect(page.get_by_role("heading", name="Report an Issue")).to_be_visible()

            # Check description value
            # Note: textarea value check
            expect(page.locator("textarea")).to_have_value("Detected pothole using Smart Scanner.")

            # Take screenshot of Report Form
            page.screenshot(path="/home/jules/verification/report_form_prefilled.png")

            print("Verification Successful!")

        except Exception as e:
            print(f"Test failed: {e}")
            page.screenshot(path="/home/jules/verification/failure.png")
            raise e
        finally:
            browser.close()

if __name__ == "__main__":
    run_test()
