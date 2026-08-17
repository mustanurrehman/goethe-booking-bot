"""Deeper inspection of exam page structure."""
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
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

url = "https://www.goethe.de/ins/pk/en/spr/prf/gzb1.cfm"
driver.get(url)
time.sleep(8)

print("=== Iframes ===")
iframes = driver.find_elements(By.TAG_NAME, "iframe")
print(f"Found {len(iframes)} iframe(s)")
for i, f in enumerate(iframes):
    print(f"  [{i}] src={f.get_attribute('src')} id={f.get_attribute('id')}")

print("\n=== pr_finder elements ===")
for sel in ["#pr_finder_9523459", ".pr-finder", "[class*='finder']", "[id*='finder']", "[id*='pr_finder']"]:
    els = driver.find_elements(By.CSS_SELECTOR, sel)
    print(f"  {sel}: {len(els)} found")
    for e in els:
        print(f"    tag={e.tag_name} displayed={e.is_displayed()} html={e.get_attribute('outerHTML')[:200]}")

print("\n=== All elements with 'standard' class ===")
all_std = driver.find_elements(By.XPATH, "//*[contains(@class, 'standard')]")
print(f"Found {len(all_std)}")
for e in all_std:
    print(f"  tag={e.tag_name} displayed={e.is_displayed()} html={e.get_attribute('outerHTML')[:200]}")

print("\n=== Body text (first 2000 chars) ===")
body = driver.find_element(By.TAG_NAME, "body")
print(body.text[:2000])

driver.quit()
