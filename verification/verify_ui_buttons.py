
from playwright.sync_api import sync_playwright, expect
import os

def run():
    os.makedirs("/home/jules/verification", exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            print("Navigating to Home...")
            page.goto("http://localhost:5173/home")
            page.wait_for_timeout(2000) # Wait for hydration

            # Verify "Traffic Sign" button
            print("Checking for Traffic Sign button...")
            traffic_btn = page.get_by_text("Traffic Sign")
            expect(traffic_btn).to_be_visible()
            print("Traffic Sign button found.")

            # Verify "Abandoned Vehicle" button
            print("Checking for Abandoned Vehicle button...")
            vehicle_btn = page.get_by_text("Abandoned Vehicle")
            expect(vehicle_btn).to_be_visible()
            print("Abandoned Vehicle button found.")

            # Take screenshot of the Road & Traffic section
            # We can try to locate the section by heading "Road & Traffic" or just full page
            print("Taking screenshot...")
            page.screenshot(path="/home/jules/verification/home_buttons.png", full_page=True)
            print("Screenshot saved to /home/jules/verification/home_buttons.png")

        except Exception as e:
            print(f"Error: {e}")
            page.screenshot(path="/home/jules/verification/error.png")
            raise
        finally:
            browser.close()

if __name__ == "__main__":
    run()
