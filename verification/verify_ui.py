from playwright.sync_api import sync_playwright, expect
import time
import os

def verify_ui(page):
    print("Navigating to home...")
    page.goto("http://localhost:5173")

    # Wait for page to load
    print("Waiting for VishwaGuru text...")
    page.wait_for_selector("text=VishwaGuru", timeout=30000)

    # Check for Civic Eye button
    print("Looking for Civic Eye button...")
    civic_eye_btn = page.get_by_text("Civic Eye")
    expect(civic_eye_btn).to_be_visible()

    # Navigate to Civic Eye
    print("Clicking Civic Eye...")
    civic_eye_btn.click()

    # Verify Civic Eye Page
    print("Waiting for Civic Eye scanner...")
    # The title in DetectorWrapper is "Civic Eye Scanner"
    expect(page.get_by_text("Civic Eye Scanner")).to_be_visible()

    # Screenshot Civic Eye
    print("Taking screenshot 1...")
    page.screenshot(path="/home/jules/verification/civic_eye.png")

    # Go back
    print("Going back...")
    page.get_by_text("Back to Home").click()

    # Check Camera Check
    print("Clicking Camera Check...")
    camera_check_btn = page.get_by_text("Camera Check")
    camera_check_btn.click()

    # Verify Modal
    print("Checking Modal...")
    expect(page.get_by_text("Camera Diagnostics")).to_be_visible()

    # Wait for active status (fake media stream should be fast)
    time.sleep(2)

    print("Taking screenshot 2...")
    page.screenshot(path="/home/jules/verification/camera_check.png")
    print("Done.")

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream"])
        context = browser.new_context(permissions=["camera"])
        page = context.new_page()
        try:
            verify_ui(page)
        except Exception as e:
            print(f"Error: {e}")
            page.screenshot(path="/home/jules/verification/error.png")
        finally:
            browser.close()
