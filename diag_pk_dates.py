#!/usr/bin/env python3
"""Dump the Pakistan B1 finder table: each exam row = dates, city, price,
bookable-from. Observe ONLY."""
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
    driver.get(URL)
    time.sleep(6)

    # Rows of the finder table
    rows = driver.find_elements(By.CSS_SELECTOR, "#pr_finder_9523489 tr, .pr-finder tr, table tr")
    print(f"Table rows found: {len(rows)}\n")
    for r in rows:
        try:
            txt = norm(r.text)
            if len(txt) < 8:
                continue
            # is this a row with a date or city or booking?
            if any(k in txt for k in ["20", "2026", "karachi", "islamabad", "lahore", "bookable", "full", "pkr", "price", "registration", "online"]):
                print(f"  ROW: {txt[:180]}")
        except Exception:
            pass

    # Date-like tokens across whole body with city context is hard; also dump finder container text fully
    try:
        fid = driver.find_element(By.CSS_SELECTOR, "#pr_finder_9523489")
        full = norm(fid.text)
        print("\n=== FULL FINDER TEXT ===")
        print(full[:1500])
    except Exception as e:
        print("no finder container:", e)

    print("\n== DONE — observed only ==")

if __name__ == "__main__":
    main()
