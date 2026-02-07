import time
from playwright.sync_api import sync_playwright

def test_new_features():
    with sync_playwright() as p:
        # Use a fake device for media stream to allow camera/mic permissions
        browser = p.chromium.launch(
            args=[
                "--use-fake-ui-for-media-stream",
                "--use-fake-device-for-media-stream"
            ]
        )
        context = browser.new_context(
            permissions=["camera", "microphone"],
            base_url="http://localhost:5173"
        )
        page = context.new_page()

        print("Navigating to Home...")
        page.goto("/")
        time.sleep(2)

        # Check for My Reports button (text "My Reports")
        print("Checking My Reports...")
        my_reports_btn = page.get_by_text("My Reports")
        assert my_reports_btn.is_visible()
        my_reports_btn.click()
        time.sleep(1)
        # Should be on /my-reports
        assert "my-reports" in page.url
        print("✅ My Reports navigation works")

        # Go back
        page.goto("/")
        time.sleep(1)

        # Check for Noise button (text "Noise")
        print("Checking Noise Detector...")
        noise_btn = page.get_by_text("Noise", exact=True)
        # It might be in a list, verify it's clickable
        assert noise_btn.is_visible()
        noise_btn.click()
        time.sleep(1)
        assert "noise" in page.url
        # Check if Start Monitoring button exists
        assert page.get_by_text("Start Monitoring").is_visible()
        print("✅ Noise Detector navigation works")

        # Go back
        page.goto("/")
        time.sleep(1)

        # Check for Civic Eye (text "Civic Eye")
        print("Checking Civic Eye...")
        civic_eye_btn = page.get_by_text("Civic Eye", exact=True)
        assert civic_eye_btn.is_visible()
        civic_eye_btn.click()
        time.sleep(1)
        assert "safety-check" in page.url
        # Check if Analyze Scene button exists
        assert page.get_by_text("Analyze Scene").is_visible()
        print("✅ Civic Eye navigation works")

        browser.close()

if __name__ == "__main__":
    try:
        test_new_features()
        print("✅ All new feature tests passed!")
    except Exception as e:
        print(f"❌ Test failed: {e}")
