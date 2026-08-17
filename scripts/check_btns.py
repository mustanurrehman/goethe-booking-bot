"""Visit A1, A2, B1 exam pages and grab the booking button HTML."""
import sys, os, time, logging
sys.path.insert(0, r'C:\Users\brosp\Downloads\goethe-bot')
os.chdir(r'C:\Users\brosp\Downloads\goethe-bot')

from booking_helper import create_driver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("check")

urls = {
    "A1": "https://www.goethe.de/ins/pk/en/spr/prf/gzsd1.cfm",
    "A2": "https://www.goethe.de/ins/pk/en/spr/prf/gzsd2.cfm",
    "B1": "https://www.goethe.de/ins/pk/en/spr/prf/gzb1.cfm",
}

for level, url in urls.items():
    print(f"\n{'='*50}")
    print(f"  {level}: {url}")
    print('='*50)
    driver = create_driver(use_headless=True, logger=logger)
    try:
        driver.get(url)
        time.sleep(5)
        buttons = driver.find_elements(By.XPATH, "//button[contains(@class, 'standard')]")
        print(f"  Found {len(buttons)} button(s) with class 'standard':")
        for btn in buttons:
            html = btn.get_attribute('outerHTML')
            disabled = btn.get_attribute('disabled')
            visible = btn.is_displayed()
            print(f"    visible={visible} disabled={bool(disabled)}")
            print(f"    HTML: {html[:300]}")
            print()
        if not buttons:
            print("  No standard buttons found. Page text (first 2000 chars):")
            print(driver.find_element(By.TAG_NAME, "body").text[:2000])
    except Exception as e:
        print(f"  ERROR: {e}")
    finally:
        driver.quit()
