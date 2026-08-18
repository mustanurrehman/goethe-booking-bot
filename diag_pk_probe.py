#!/usr/bin/env python3
"""Probe the PAKISTAN B1 finder (ins/pk/en/spr/prf/gzb1.cfm) for ANY open
booking slots across Karachi / Islamabad / Lahore.
Observes ONLY — never clicks booking, never submits, never books.
"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from booking_helper import _find_local_driver, _detect_chrome_version

PORT = os.environ.get("REAL_CHROME_PORT", "9222")
URL = "https://www.goethe.de/ins/pk/en/spr/prf/gzb1.cfm"

def norm(t):
    return " ".join((t or "").lower().split())

def main():
    driver_path = _find_local_driver(_detect_chrome_version())
    if not driver_path:
        print("FAIL: no cached chromedriver"); return
    opts = webdriver.ChromeOptions()
    opts.add_experimental_option("debuggerAddress", f"127.0.0.1:{PORT}")
    svc = Service(driver_path)
    if os.name == "nt": svc.creation_flags = 0
    driver = webdriver.Chrome(service=svc, options=opts)
    print("Attached. Loading Pakistan B1 finder ...")
    driver.get(URL)
    time.sleep(6)
    print(f"URL: {driver.current_url[:120]}")
    print(f"TITLE: {driver.title}")

    body = driver.find_element(By.TAG_NAME, "body").text
    low = norm(body)

    # 1. Any city/location names on the page?
    for city in ["karachi", "islamabad", "lahore", "rawalpindi", "faisalabad", "multan", "hyderabad"]:
        if city in low:
            print(f"  [CITY] '{city}' appears on page")

    # 2. Any "bookable from" / book/select buttons?
    for kw in ["bookable from", "select modules", "book", "buchen", "not bookable", "fully booked", "no results", "currently no exam"]:
        idx = low.find(kw)
        if idx >= 0:
            print(f"  [KEY]: ...{norm(body)[max(0,idx-40):idx+140]}...")

    # 3. Any enabled booking buttons?
    btn_xpath = ("//*[self::a or self::button][not(@disabled)]"
        "[contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'book')"
        " or contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'select')"
        " or contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'buchen')"
        " or contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'module')]")
    btns = driver.find_elements(By.XPATH, btn_xpath)
    print(f"\n  Enabled book/select/module buttons: {len(btns)}")
    for b in btns[:10]:
        try:
            txt = (b.text or "").strip()[:60]
            cls = b.get_attribute("class") or ""
            href = b.get_attribute("href") or ""
            row = norm(driver.find_element(By.XPATH, "ancestor::*[self::tr or self::li or self::div][1]").text if False else "")
            print(f"    <{b.tag_name}> '{txt}' cl='{cls[:35]}' href='{href[:60]}'")
        except Exception: pass

    # 4. finder id + raw table/dates
    fid = driver.find_elements(By.XPATH, "//*[contains(@id,'pr_finder')]")
    print(f"\n  pr_finder elements: {len(fid)}")
    for f in fid[:3]:
        try:
            print(f"    id={f.get_attribute('id')} text={norm(f.text)[:160]}")
        except Exception: pass

    print("\n== DONE — probe observed only, nothing booked ==")

if __name__ == "__main__":
    main()
