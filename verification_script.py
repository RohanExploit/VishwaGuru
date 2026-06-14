from playwright.sync_api import sync_playwright, expect
import os

def test_auto_describe(page):
    # Mock the backend response for description
    page.route("**/api/generate-description", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body='{"description": "A generated description of a pothole"}'
    ))

    # Also mock severity detection if it triggers
    page.route("**/api/detect-severity", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body='{"level": "Medium", "raw_label": "pothole", "confidence": 0.8}'
    ))

    # Go to Home page
    page.goto("http://localhost:5173")

    # Wait for page load
    page.wait_for_timeout(2000)

    # Find "Report Issue" button and click
    # The button has text "Report Issue" inside a span, and it's a button.
    # page.get_by_role("button", name="Report Issue") might work if "Report Issue" is the accessible name.
    # Since it contains an icon and a span, let's use get_by_text to be safe or verify accessible name.

    page.get_by_text("Report Issue").click()

    # Verify we are on Report Form
    expect(page.get_by_role("heading", name="Report an Issue")).to_be_visible()

    # Upload an image
    with open("dummy.jpg", "wb") as f:
        f.write(b"dummy image content")

    # There are two file inputs (upload and camera). We want the upload one.
    # The upload one is hidden but associated with a label "Upload".
    # Playwright's set_input_files works on hidden inputs if we select them.
    # We can select by looking for the input inside the label with text "Upload".

    # The structure is: label > span("Upload") + input[type="file"]
    # We can select the input that is inside the label containing "Upload".

    # Or just select the first file input as there are two.
    # The first one is upload, second is camera.
    page.locator('input[type="file"]').first.set_input_files("dummy.jpg")

    # Wait for "Auto-fill description from image" button to appear
    # The text is "✨ Auto-fill description from image" or "Generating description..."
    auto_describe_btn = page.get_by_role("button", name="Auto-fill description from image")
    expect(auto_describe_btn).to_be_visible()

    # Click it
    auto_describe_btn.click()

    # Verify description is updated
    expect(page.locator("textarea")).to_have_value("A generated description of a pothole")

    # Screenshot
    page.screenshot(path="/home/jules/verification/verification.png")

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            test_auto_describe(page)
            print("Verification script finished successfully.")
        except Exception as e:
            print(f"Error: {e}")
            page.screenshot(path="/home/jules/verification/error.png")
        finally:
            browser.close()
