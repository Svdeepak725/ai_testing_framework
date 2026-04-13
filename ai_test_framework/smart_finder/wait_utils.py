from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Utility to wait for element to be interactable
# Usage: wait_for_interactable(driver, By.XPATH, xpath)
def wait_for_interactable(driver, by, value, timeout=10):
    wait = WebDriverWait(driver, timeout)
    return wait.until(EC.element_to_be_clickable((by, value)))
