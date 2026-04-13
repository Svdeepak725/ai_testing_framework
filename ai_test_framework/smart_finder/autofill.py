
import os
from datetime import datetime
from selenium.webdriver.common.by import By
from smart_finder.wait_utils import wait_for_interactable


class SmartAutoFill:

    def __init__(self, smart_finder):
        self.finder = smart_finder

    def _ensure_dir(self, path):
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)

    def _save_screenshot(self, driver, dirpath, prefix="screenshot"):
        self._ensure_dir(dirpath)
        ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        fname = f"{prefix}_{ts}.png"
        dest = os.path.join(dirpath, fname)
        try:
            driver.save_screenshot(dest)
            print(f"📷 Screenshot saved: {dest}")
        except Exception as e:
            print(f"⚠️ Failed to save screenshot: {e}")

    def _auto_find_submit(self, timeout=5):
        # Try common submit selectors in order of priority
        driver = self.finder.driver
        candidates = [
            (By.XPATH, "//input[@type='submit']"),
            (By.XPATH, "//button[@type='submit']"),
            (By.XPATH, "//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'sign in')]") ,
            (By.XPATH, "//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'log in')]") ,
            (By.XPATH, "//input[@type='button' and (contains(translate(@value, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'sign in') or contains(translate(@value, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'log in') or contains(translate(@value, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'login'))]")
        ]
        for by, value in candidates:
            try:
                el = wait_for_interactable(driver, by, value, timeout=timeout)
                if el:
                    return el
            except Exception:
                continue
        return None

    def fill_form(self, data: dict, timeout=10, submit_query: str = None, screenshot_dir: str = "screenshots"):
        driver = self.finder.driver
        # Fill each field
        for key, value in data.items():
            try:
                # Wait for element to be interactable before filling
                element = self.finder.find(key, wait_interactable=True, timeout=timeout)

                try:
                    element.clear()
                except Exception:
                    pass

                element.send_keys(str(value))
                print(f"✔ Filled '{key}': {value}")

            except Exception as e:
                print(f"❌ Could not fill '{key}': {e}")

        # Take a screenshot after filling the form
        try:
            self._save_screenshot(driver, screenshot_dir, prefix="after_fill")
        except Exception:
            pass

        # Click submit if possible
        submit_element = None
        if submit_query:
            try:
                submit_element = self.finder.find(submit_query, wait_interactable=True, timeout=timeout)
            except Exception as e:
                print(f"⚠️ Submit button not found with query '{submit_query}': {e}")

        if submit_element is None:
            submit_element = self._auto_find_submit(timeout=timeout)

        if submit_element is not None:
            try:
                submit_element.click()
                print("▶ Clicked submit button")
                # Screenshot after click
                try:
                    self._save_screenshot(driver, screenshot_dir, prefix="after_click")
                except Exception:
                    pass
            except Exception as e:
                    # Try JS click as a fallback
                    try:
                        driver.execute_script("arguments[0].click();", submit_element)
                        print("▶ Clicked submit button (via JS)")
                        try:
                            self._save_screenshot(driver, screenshot_dir, prefix="after_click")
                        except Exception:
                            pass
                    except Exception as e2:
                        print(f"❌ Failed to click submit button: {e}; fallback JS click failed: {e2}")
        else:
            print("⚠️ No submit button found to click")

