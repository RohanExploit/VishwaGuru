from playwright.sync_api import sync_playwright

def test_verify_detectors():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Debug console
        page.on("console", lambda msg: print(f"Console: {msg.text}"))
        page.on("pageerror", lambda exc: print(f"PageError: {exc}"))
        page.on("requestfailed", lambda req: print(f"RequestFailed: {req.url} {req.failure}"))

        # Mock Auth and API calls to bypass backend dependency and login
        page.route("**/auth/me", lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body='{"id": 1, "email": "test@example.com", "role": "user", "full_name": "Test User"}'
        ))
        page.route("**/api/issues/recent*", lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body='[]'
        ))
        page.route("**/api/mh/responsibility-map", lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body='{}'
        ))
        page.route("**/api/stats", lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body='{"total_issues": 100, "resolved_issues": 50, "pending_issues": 50}'
        ))

        # Navigate to login first to ensure localStorage context
        print("Navigating to /login...")
        page.goto("http://localhost:5173/login")

        # Simulate successful login by setting token
        print("Setting token...")
        page.evaluate("localStorage.setItem('token', 'fake-jwt-token')")

        # Navigate to Home (force reload to pick up token in useState initializer)
        print("Navigating to /...")
        page.goto("http://localhost:5173/")

        # Wait for home page content
        print("Waiting for content...")
        try:
            page.wait_for_selector("text=Community Impact", timeout=10000)
        except Exception as e:
            print(f"Timeout waiting for Home page: {e}")
            page.screenshot(path="verification/debug_timeout.png")
            browser.close()
            return

        # Check for new buttons
        detectors = [
            "Air Quality",
            "Playground Safety",
            "Public Transport",
            "Cleanliness",
            "Traffic Sign",
            "Abandoned Vehicle"
        ]

        missing = []
        for det in detectors:
            found = False
            try:
                # Use a flexible locator
                locator = page.get_by_text(det, exact=False).first
                if locator.count() > 0:
                    locator.scroll_into_view_if_needed()
                    if locator.is_visible():
                        print(f"Found detector: {det}")
                        found = True
            except Exception:
                pass

            if not found:
                missing.append(det)

        # Take screenshot
        page.screenshot(path="verification/verification.png", full_page=True)

        if missing:
            print(f"Missing detectors: {missing}")
        else:
            print("All detectors found!")

        browser.close()

if __name__ == "__main__":
    test_verify_detectors()
