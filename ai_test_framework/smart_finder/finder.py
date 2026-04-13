
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from ai_locator.engine import AILocatorEngine
from smart_finder.wait_utils import wait_for_interactable


class SmartFinder:

    def __init__(self, driver, locator_file="locators.json"):
        self.driver = driver
        self.engine = AILocatorEngine(locator_file)

    def find(self, query, wait_interactable=True, timeout=10):
        best = self.engine.best_match(query)

        if not best:
            raise Exception("No matching element found!")

        # Prefer waiting for the xpath to be clickable.
        if wait_interactable:
            try:
                return wait_for_interactable(self.driver, By.XPATH, best["xpath"], timeout)
            except TimeoutException as e:
                # Helpful debug output
                print(f"⚠️ wait_for_interactable timed out for xpath: {best.get('xpath')}")
                # Try CSS selector fallback if available
                css = best.get("css")
                if css:
                    try:
                        print(f"ℹ️ Trying CSS fallback: {css}")
                        return wait_for_interactable(self.driver, By.CSS_SELECTOR, css, timeout)
                    except TimeoutException:
                        print(f"⚠️ CSS fallback also timed out: {css}")

                # Final fallback: try to locate the element without waiting and return it
                # (autofill has JS-click fallback). Scroll into view before returning.
                try:
                    el = self.driver.find_element(By.XPATH, best["xpath"])
                    try:
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});", el)
                    except Exception:
                        pass
                    print("ℹ️ Located element by XPath without waiting; returning it for manual/JS click")
                    return el
                except NoSuchElementException:
                    # Try searching inside iframes as a last effort
                    print("ℹ️ Element not found in main document; searching inside iframes...")
                    frames = self.driver.find_elements(By.TAG_NAME, "iframe")
                    original_handle = None
                    try:
                        for idx, frame in enumerate(frames):
                            try:
                                # switch into frame
                                self.driver.switch_to.frame(frame)
                                print(f"ℹ️ Switched into iframe {idx}")
                                # try xpath then css then no-wait find
                                try:
                                    el = wait_for_interactable(self.driver, By.XPATH, best["xpath"], timeout)
                                    return el
                                except Exception:
                                    pass
                                if css:
                                    try:
                                        el = wait_for_interactable(self.driver, By.CSS_SELECTOR, css, timeout)
                                        return el
                                    except Exception:
                                        pass
                                try:
                                    el = self.driver.find_element(By.XPATH, best["xpath"])
                                    try:
                                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});", el)
                                    except Exception:
                                        pass
                                    print(f"ℹ️ Located element inside iframe {idx} by XPath")
                                    return el
                                except Exception:
                                    # not found in this frame — continue
                                    pass
                            finally:
                                # switch back to top to continue searching other frames
                                self.driver.switch_to.default_content()
                        # if loop completes, element not found
                        raise Exception("Element found by AI locator could not be located on the page or inside iframes")
                    finally:
                        # ensure we are back to default content
                        try:
                            self.driver.switch_to.default_content()
                        except Exception:
                            pass
        else:
            # No waiting requested — try CSS first, then xpath
            css = best.get("css")
            if css:
                try:
                    return self.driver.find_element(By.CSS_SELECTOR, css)
                except Exception:
                    pass
            return self.driver.find_element(By.XPATH, best["xpath"])
