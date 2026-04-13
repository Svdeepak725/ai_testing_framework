import os
import sys
import time
import argparse
import datetime
from pathlib import Path
from selenium import webdriver

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from utils.file_utils import generate_unique_locators_filename, archive_file, purge_older_files

from locator_scanner.scanner import PageScanner
from smart_finder.finder import SmartFinder
from smart_finder.autofill import SmartAutoFill

def main(output_path=None):
    driver = webdriver.Chrome()
    driver.get("https://profile.w3schools.com/login")
    driver.maximize_window()

    # Step 1: Scan page
    scanner = PageScanner(driver)
    output = output_path or os.getenv('LOCATORS_OUTPUT', None)
    if not output:
        # create unique per-run locators file in package root
        output = generate_unique_locators_filename(output_dir=Path(__file__).resolve().parents[1])
    else:
        output = Path(output)
    scanner.scan_page(output)
    print(f"✔ Scan complete, locators saved to: {output}")

    # Step 2: AI Finder (pass the output file to engine so it reads the scanned locators)
    finder = SmartFinder(driver, locator_file=str(output))

    # Step 3: AutoFill
    auto = SmartAutoFill(finder)

    auto.fill_form({
    "email": "dhoni771993@gmail.com",
    "password": "Vijisundar@725"
})

    # Step 4: Optional explicit login click.
    # AutoFill may have already submitted, so do not fail the run if this element is not available.
    try:
        login_btn = finder.find("login button", wait_interactable=True)
        login_btn.click()
    except Exception as e:
        print(f"⚠️ Skipping explicit login click: {e}")

    # Wait for page to load after login (2 seconds for redirect/response)
    time.sleep(2)
    
    # Take final screenshot showing login result (success page or error message)
    screenshot_dir = Path(__file__).resolve().parents[1] / "screenshots"
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now(datetime.UTC).strftime("%Y%m%dT%H%M%SZ")
    final_screenshot = screenshot_dir / f"login_result_{ts}.png"
    try:
        driver.save_screenshot(str(final_screenshot))
        print(f"📷 Final screenshot (login result) saved: {final_screenshot}")
    except Exception as e:
        print(f"⚠️ Failed to save final screenshot: {e}")
    
    # Close browser
    try:
        driver.quit()
    except Exception:
        pass

    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Test demo using AI locator')
    parser.add_argument('--locators-output', dest='locators_output', help='Path to write locators JSON', default=None)
    parser.add_argument('--no-archive', dest='no_archive', action='store_true', help='Do not archive the locators file after test (default archives)')
    parser.add_argument('--purge-days', dest='purge_days', type=int, default=None, help='If set, purge archive files older than this many days')
    args = parser.parse_args()
    loc_file = main(output_path=args.locators_output)

    # post-run: archive or purge based on flags/env
    archive = not args.no_archive
    purge_days = args.purge_days
    if archive and loc_file:
        try:
            archive_file(loc_file)
        except Exception as e:
            print('Warning, archive failed:', e)

    if purge_days is not None:
        try:
            archive_dir = Path(__file__).resolve().parents[1] / 'locators_archive'
            removed = purge_older_files(archive_dir, days=purge_days)
            print(f'Purged {removed} archived files older than {purge_days} days')
        except Exception as e:
            print('Warning, purge failed:', e)
