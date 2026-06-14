from playwright.sync_api import Page, expect, sync_playwright
import os

def verify_new_detectors(page: Page):
    # Intercept API calls to mock backend
    def handle_login(route):
        print(f"Intercepted login: {route.request.url}")
        route.fulfill(status=200, json={
            "access_token": "mock_token",
            "token_type": "bearer",
            "user": {
                "id": 1,
                "email": "test@example.com",
                "full_name": "Test User",
                "role": "user"
            }
        })

    def handle_me(route):
        route.fulfill(status=200, json={
            "id": 1,
            "email": "test@example.com",
            "full_name": "Test User",
            "role": "user"
        })

    def handle_issues_recent(route):
        route.fulfill(status=200, json=[])

    def handle_stats(route):
        route.fulfill(status=200, json={
            "total_issues": 100,
            "resolved_issues": 50,
            "pending_issues": 50
        })

    def handle_responsibility_map(route):
        route.fulfill(status=200, json={})

    # Register intercepts
    page.route("**/auth/login", handle_login)
    page.route("**/auth/me", handle_me)
    page.route("**/api/issues/recent**", handle_issues_recent)
    page.route("**/api/stats", handle_stats)
    page.route("**/api/misc/responsibility-map", handle_responsibility_map)
    page.route("**/api/leaderboard", lambda route: route.fulfill(status=200, json=[]))

    # Go to login page directly
    print("Navigating to login page...")
    page.goto("http://localhost:5173/login")

    print("Logging in...")
    page.get_by_label("Email address").fill("test@example.com")
    page.get_by_label("Password").fill("password")
    page.get_by_role("button", name="Sign In").click()

    # Wait for navigation to Home (root)
    # Note: Login success redirects to '/' (Home)
    page.wait_for_url("http://localhost:5173/")

    print("On Home page.")
    # Check for new detector buttons
    # "Air Quality", "Playground", "Public Transport", "Cleanliness"

    # We might need to scroll down or wait for content to load
    page.wait_for_timeout(2000) # Wait for animations/load

    expect(page.get_by_text("Air Quality")).to_be_visible()
    print("Found 'Air Quality'")

    expect(page.get_by_text("Playground")).to_be_visible()
    print("Found 'Playground'")

    expect(page.get_by_text("Cleanliness")).to_be_visible()
    print("Found 'Cleanliness'")

    expect(page.get_by_text("Public Transport")).to_be_visible()
    print("Found 'Public Transport'")

    # Click on one to verify navigation (optional, but good)
    page.get_by_text("Air Quality").click()
    page.wait_for_url("**/air-quality")
    expect(page.get_by_text("Air Quality Monitor")).to_be_visible()
    print("Navigated to Air Quality Detector successfully")

    # Take screenshot
    os.makedirs("/home/jules/verification", exist_ok=True)
    page.screenshot(path="/home/jules/verification/new_detectors.png", full_page=True)
    print("Screenshot taken.")

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            verify_new_detectors(page)
        except Exception as e:
            print(f"Verification failed: {e}")
            page.screenshot(path="/home/jules/verification/failure.png")
            raise e
        finally:
            browser.close()
