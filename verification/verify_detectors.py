import time
from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # Listen for console errors
        page.on("console", lambda msg: print(f"CONSOLE: {msg.text}") if msg.type == "error" else None)
        page.on("pageerror", lambda exc: print(f"PAGE ERROR: {exc}"))

        print("Navigating to home page...")
        page.goto("http://localhost:5173/")

        try:
             page.wait_for_load_state("networkidle", timeout=5000)
        except:
             pass

        try:
            cta_button = page.get_by_text("Call Action Issue")
            if cta_button.count() > 0 and cta_button.first.is_visible():
                print("Landing page detected. Clicking 'Call Action Issue'...")
                cta_button.first.click()
                page.wait_for_url("**/home")
                print("Navigated to Home page.")
        except Exception as e:
            print(f"Landing page check skipped or failed: {e}")

        # Wait for Home page
        try:
            category_title = page.locator("text=Road & Traffic")
            category_title.wait_for(state="visible", timeout=10000)

            # Scroll to it
            category_title.scroll_into_view_if_needed()
            page.wait_for_timeout(1000)

        except Exception as e:
            print(f"Failed to find/scroll to 'Road & Traffic'. Error: {e}")
            page.screenshot(path="verification/error_home_scroll.png")
            browser.close()
            return

        # Verify Traffic Sign Detector
        print("Checking for Traffic Sign detector...")
        try:
            traffic_btn = page.locator("button").filter(has_text="Traffic Sign").first

            if traffic_btn.is_visible():
                 print("Found Traffic Sign button. Clicking...")
                 traffic_btn.click()
            else:
                 print("Traffic Sign button NOT visible. Scrolling...")
                 page.evaluate("window.scrollBy(0, 500)")
                 page.wait_for_timeout(1000)
                 if traffic_btn.is_visible():
                      traffic_btn.click()
                 else:
                      print("Still not visible. Trying force click.")
                      traffic_btn.click(force=True)

            # Check if navigation happened
            try:
                page.wait_for_url("**/traffic-sign", timeout=5000)
                print("Navigated to /traffic-sign")
            except:
                print(f"Failed to navigate. Current URL: {page.url}")
                page.screenshot(path="verification/error_traffic_nav.png")
                raise

            # Check for title (h2 based on GenericDetector)
            print("Waiting for Traffic Sign header...")
            page.wait_for_selector("h2:has-text('Traffic Sign')", timeout=10000)

            # Check for instructions
            print("Waiting for instructions...")
            page.wait_for_selector("text=Point camera at a damaged or vandalized traffic sign.")

            # Check for Capture Photo button
            print("Waiting for Capture Photo button...")
            page.wait_for_selector("button:has-text('Capture Photo')")

            print("SUCCESS: Traffic Sign Detector page verified.")
            page.screenshot(path="verification/success_traffic_sign.png")

            # Navigate back to Home directly instead of relying on Back button
            print("Navigating back to Home...")
            page.goto("http://localhost:5173/home")
            page.wait_for_selector("text=Road & Traffic", timeout=10000)
            category_title = page.locator("text=Road & Traffic")
            category_title.scroll_into_view_if_needed()

        except Exception as e:
            print(f"FAILURE: Traffic Sign Detector verification failed: {e}")
            page.screenshot(path="verification/error_traffic_sign.png")
            # Try to recover by going home
            page.goto("http://localhost:5173/home")
            page.wait_for_selector("text=Road & Traffic", timeout=10000)

        # Verify Abandoned Vehicle Detector
        print("Checking for Abandoned Vehicle detector...")
        try:
            # Need to scroll to find it if it's further down or if we reset
            category_title = page.locator("text=Road & Traffic")
            category_title.scroll_into_view_if_needed()

            vehicle_btn = page.locator("button").filter(has_text="Abandoned Vehicle").first

            if vehicle_btn.is_visible():
                 print("Found Abandoned Vehicle button. Clicking...")
                 vehicle_btn.click()
            else:
                 print("Abandoned Vehicle button NOT visible. Scrolling/Force clicking...")
                 page.evaluate("window.scrollBy(0, 500)")
                 if vehicle_btn.is_visible():
                      vehicle_btn.click()
                 else:
                      vehicle_btn.click(force=True)

            try:
                page.wait_for_url("**/abandoned-vehicle", timeout=5000)
                print("Navigated to /abandoned-vehicle")
            except:
                 print(f"Failed to navigate. Current URL: {page.url}")
                 raise

            # Check for title
            print("Waiting for Abandoned Vehicle header...")
            page.wait_for_selector("h2:has-text('Abandoned Vehicle')", timeout=10000)

            print("Waiting for Capture Photo button...")
            page.wait_for_selector("button:has-text('Capture Photo')")

            print("SUCCESS: Abandoned Vehicle Detector page verified.")
            page.screenshot(path="verification/success_abandoned_vehicle.png")

        except Exception as e:
            print(f"FAILURE: Abandoned Vehicle Detector verification failed: {e}")
            page.screenshot(path="verification/error_abandoned_vehicle.png")

        # Navigate back to Home
        print("Navigating back to Home...")
        page.goto("http://localhost:5173/home")

        # Public Facilities (Management category)
        print("Checking for Public Facilities detector...")
        try:
             # Management might be further down
             page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
             page.wait_for_timeout(1000)

             # Try stricter locator
             pub_btn = page.locator("button").filter(has_text="Public Facilities").first
             if not pub_btn.is_visible():
                  # Maybe scroll up a bit
                  page.evaluate("window.scrollBy(0, -500)")
                  page.wait_for_timeout(500)

             if pub_btn.is_visible():
                  pub_btn.click()
             else:
                  # Fallback
                  print("Button not found via locator, trying text search")
                  page.get_by_text("Public Facilities").click()

             page.wait_for_url("**/public-facilities", timeout=5000)
             page.wait_for_selector("h2:has-text('Public Facilities Detector')", timeout=10000)
             page.wait_for_selector("button:has-text('Capture Photo')")
             print("SUCCESS: Public Facilities Detector verified.")
             page.screenshot(path="verification/success_public_facilities.png")
             page.goto("http://localhost:5173/home")
        except Exception as e:
             print(f"FAILURE: Public Facilities Detector failed: {e}")
             page.screenshot(path="verification/error_public_facilities.png")
             page.goto("http://localhost:5173/home")

        # Construction Safety (Environment category)
        print("Checking for Construction Safety detector...")
        try:
             page.evaluate("window.scrollTo(0, 500)")
             page.wait_for_timeout(1000)
             const_btn = page.locator("button").filter(has_text="Construction Safety").first
             if const_btn.is_visible():
                  const_btn.click()
             else:
                  page.get_by_text("Construction Safety").click()

             page.wait_for_url("**/construction-safety", timeout=5000)
             page.wait_for_selector("h2:has-text('Construction Safety')", timeout=10000)
             page.wait_for_selector("button:has-text('Capture Photo')")
             print("SUCCESS: Construction Safety Detector verified.")
             page.screenshot(path="verification/success_construction_safety.png")
             page.goto("http://localhost:5173/home")
        except Exception as e:
             print(f"FAILURE: Construction Safety Detector failed: {e}")
             page.screenshot(path="verification/error_construction_safety.png")
             page.goto("http://localhost:5173/home")

        # Water Leak (Environment category)
        print("Checking for Water Leak detector...")
        try:
             page.evaluate("window.scrollTo(0, 500)")
             page.wait_for_timeout(1000)
             water_btn = page.locator("button").filter(has_text="Water Leak").first
             if water_btn.is_visible():
                  water_btn.click()
             else:
                  page.get_by_text("Water Leak").click()

             page.wait_for_url("**/water-leak", timeout=5000)
             page.wait_for_selector("h2:has-text('Live Water Leak Detector')", timeout=10000)
             page.wait_for_selector("button:has-text('Start Live Detection')")
             print("SUCCESS: Water Leak Detector verified.")
             page.screenshot(path="verification/success_water_leak.png")
             page.goto("http://localhost:5173/home")
        except Exception as e:
             print(f"FAILURE: Water Leak Detector failed: {e}")
             page.screenshot(path="verification/error_water_leak.png")
             page.goto("http://localhost:5173/home")

        # Crowd Detector (Environment category)
        print("Checking for Crowd detector...")
        try:
             page.evaluate("window.scrollTo(0, 500)")
             page.wait_for_timeout(1000)
             crowd_btn = page.locator("button").filter(has_text="Crowd").first
             if crowd_btn.is_visible():
                  crowd_btn.click()
             else:
                  page.get_by_text("Crowd").click()

             page.wait_for_url("**/crowd", timeout=5000)
             page.wait_for_selector("h2:has-text('Crowd Density Monitor')", timeout=10000)
             page.wait_for_selector("button:has-text('Start Live Detection')")
             print("SUCCESS: Crowd Detector verified.")
             page.screenshot(path="verification/success_crowd.png")
             page.goto("http://localhost:5173/home")
        except Exception as e:
             print(f"FAILURE: Crowd Detector failed: {e}")
             page.screenshot(path="verification/error_crowd.png")
             page.goto("http://localhost:5173/home")

        browser.close()

if __name__ == "__main__":
    run()
