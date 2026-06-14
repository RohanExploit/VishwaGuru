import os
from playwright.sync_api import sync_playwright, expect

def verify_home_route():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Navigate to /home
        print("Navigating to http://localhost:5173/home")
        page.goto("http://localhost:5173/home")

        # Wait for Home page content
        print("Waiting for Home page content...")
        # Check for "Report Issue" button which is on Home
        page.wait_for_selector("text=Report Issue", timeout=10000)

        # Take a screenshot
        page.screenshot(path="/home/jules/verification/home_route.png")
        print("Screenshot saved to /home/jules/verification/home_route.png")

        browser.close()

if __name__ == "__main__":
    os.makedirs("/home/jules/verification", exist_ok=True)
    try:
        verify_home_route()
    except Exception as e:
        print(f"Verification failed: {e}")
