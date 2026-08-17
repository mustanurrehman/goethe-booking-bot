"""Fix chromedriver and scrape A1/A2/B1 buttons."""
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--window-size=1920,1080")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)

urls = {
    "A1": "https://www.goethe.de/ins/pk/en/spr/prf/gzsd1.cfm",
    "A2": "https://www.goethe.de/ins/pk/en/spr/prf/gzsd2.cfm",
    "B1": "https://www.goethe.de/ins/pk/en/spr/prf/gzb1.cfm",
}

try:
    for level, url in urls.items():
        print(f"\n=== {level} ===")
        driver.get(url)
        time.sleep(5)
        
        btns = driver.find_elements("xpath", "//button[contains(@class, 'standard')]")
        print(f"  Found {len(btns)} button(s) with 'standard' class:")
        for b in btns:
            if b.is_displayed():
                print(f"  visible: {b.get_attribute('outerHTML')[:350]}")
        
        if not btns:
            print("  No standard buttons. Scanning for booking text...")
            for kw in ["Select module", "Bookable", "Book now", "Buchen"]:
                els = driver.find_elements("xpath", 
                    f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{kw.lower()}')]")
                for el in els:
                    if el.is_displayed():
                        tag = el.tag_name
                        html = el.get_attribute("outerHTML")[:300]
                        print(f"  [{tag}] matched '{kw}': {html}")
finally:
    driver.quit()
