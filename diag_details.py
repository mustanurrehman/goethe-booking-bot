#!/usr/bin/env python3
"""Click the DETAILS button on an exam card and dump what opens.
Tells us the real booking entry point (modal / book button / page change).
"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from booking_helper import _find_local_driver, _detect_chrome_version

PORT = os.environ.get("REAL_CHROME_PORT", "9222")
URL = os.environ.get("DIAG_URL", "https://www.goethe.de/ins/in/en/spr/prf/gzb1.cfm")

def main():
    driver_path = _find_local_driver(_detect_chrome_version())
    if not driver_path:
        print("FAIL: no cached chromedriver")
        return
    opts = webdriver.ChromeOptions()
    opts.add_experimental_option("debuggerAddress", f"127.0.0.1:{PORT}")
    svc = Service(driver_path)
    if os.name == "nt":
        svc.creation_flags = 0
    driver = webdriver.Chrome(service=svc, options=opts)
    print(f"Attached. URL now: {driver.current_url[:80]}")

    print(f"Loading {URL} ...")
    driver.get(URL)
    time.sleep(5)
    print(f"Title: {driver.title}")

    # Find DETAILS buttons in the finder cards
    details = driver.find_elements(By.XPATH,
        "//*[self::a or self::button][contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'details')]")
    print(f"\nDETAILS buttons found: {len(details)}")
    if not details:
        print("(none — maybe booking is disabled entirely)")
        return

    # Also count any book/select buttons present
    booky = driver.find_elements(By.XPATH,
        "//*[self::a or self::button][contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'book')"
        " or contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'select')]")
    print(f"'book/select' buttons found: {len(booky)}")

    # Click first DETAILS
    first = details[0]
    print("\nClicking first DETAILS button...")
    try:
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", first)
        time.sleep(1)
        driver.execute_script("arguments[0].click();", first)
    except Exception as e:
        print(f"Click failed: {e}")

    time.sleep(3)

    # What appeared?
    print(f"\nURL after click: {driver.current_url[:120]}")
    # Any modal / popup?
    modals = driver.find_elements(By.CSS_SELECTOR, ".modal, .modal-dialog, [class*='modal'], [role='dialog'], [class*='popup'], [class*='drawer']")
    print(f"Modal/dialog elements: {len(modals)}")
    for m in modals[:5]:
        try:
            txt = (m.text or "").strip()[:400].replace("\n", " | ")
            cls = m.get_attribute("class") or ""
            if txt:
                print(f"  MODAL class='{cls[:50]}' text: {txt}")
        except Exception:
            pass

    # Book/select buttons now?
    booky2 = driver.find_elements(By.XPATH,
        "//*[self::a or self::button][contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'book')"
        " or contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'select')"
        " or contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'weiter')]")
    print(f"\n'book/select/weiter' buttons after click: {len(booky2)}")
    for b in booky2[:10]:
        try:
            print(f"  <{b.tag_name}> '{b.text[:50].strip()}' class='{(b.get_attribute('class') or '')[:40]}' href='{(b.get_attribute('href') or '')[:90]}'")
        except Exception:
            pass

    # body preview
    body = driver.find_element(By.TAG_NAME, "body").text
    idx = body.lower().find("book")
    if idx >= 0:
        print(f"\nBODY mentions 'book': ...{body[max(0,idx-60):idx+120]}...")

    print("\n== DONE ==")

if __name__ == "__main__":
    main()