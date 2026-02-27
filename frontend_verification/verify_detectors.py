from playwright.sync_api import sync_playwright
import time

def verify_new_detectors():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Navigate to home
        page.goto("http://localhost:5173")
        time.sleep(2) # Wait for load

        # Login flow (using fake auth if needed, or bypass)
        # Assuming the app redirects to login if not authenticated
        # Let's try to login as a user
        if "login" in page.url:
            page.fill('input[type="email"]', 'test@example.com')
            page.fill('input[type="password"]', 'password')
            page.click('button:has-text("Login")')
            time.sleep(2)

        # Take screenshot of Home to see new categories
        page.screenshot(path="frontend_verification/home_categories.png")

        # Navigate to Construction Safety
        # Click on the button or navigate directly
        # Finding the button might be tricky with dynamic content, let's try direct navigation
        page.goto("http://localhost:5173/construction-safety")
        time.sleep(2)
        page.screenshot(path="frontend_verification/construction_safety.png")

        # Navigate to Playground Damage
        page.goto("http://localhost:5173/playground-damage")
        time.sleep(2)
        page.screenshot(path="frontend_verification/playground_damage.png")

        browser.close()

if __name__ == "__main__":
    verify_new_detectors()
