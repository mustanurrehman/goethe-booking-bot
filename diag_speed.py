#!/usr/bin/env python3
"""Full Germany DETAILS→Select-modules flow at FAST speed, watching per-step timing.
Observes ONLY — never submits final booking."""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from booking_helper import _find_local_driver, _detect_chrome_version

PORT = os.environ.get("REAL_CHROME_PORT", "9222")
URL = "https://www.goethe.de/ins/de/en/prf/ort/ham/gzb1.cfm"

def t0():
    return time.monotonic()

def main():
    driver_path = _find_local_driver(_detect_chrome_version())
    if not driver_path:
        print("FAIL: no cached chromedriver"); return
    opts = Options()
    opts.add_experimental_option("debuggerAddress", f"127.0.0.1:{PORT}")
    svc = Service(driver_path)
    if os.name == "nt": svc.creation_flags = 0
    driver = webdriver.Chrome(service=svc, options=opts)
    T = t0()
    driver.get(URL)
    time.sleep(6)
    print(f"LOAD {URL[:50]} @ {time.monotonic()-T:.1f}s -> {driver.current_url[:70]}")

    # Find "Select modules" button
    btns = driver.find_elements(By.XPATH,
        "//*[self::a or self::button][not(@disabled)]"
        "[contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'select')"
        " or contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'book')"
        " or contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'buchen')]")
    print(f"bookable btns: {len(btns)}")
    target = None
    for b in btns:
        try:
            txt = (b.text or "").strip()[:50]
            if "select module" in " ".join(txt.lower().split()):
                target = b; print(f"  -> '{txt}'"); break
        except Exception: pass
    if target is None and btns: target = btns[0]; print(f"  (fallback) '{target.text.strip()[:40]}'")
    if target is None:
        print("no button — booking not open"); return

    # Click it
    driver.execute_script("arguments[0].click();", target)
    t_click = t0()
    time.sleep(4)
    t_after = t0()
    print(f"CLICK -> waited {t_after-t_click:.1f}s; URL now: {driver.current_url[:80]}")

    # Module picker page
    cbs = driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
    print(f"  module checkboxes: {len(cbs)} (pre-checked={any(c.is_selected() for c in cbs)})")

    # Continue
    cont = driver.find_elements(By.XPATH,
        "//button[contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'continue')"
        " or contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'weiter')]")
    if cont:
        print(f"  continue btn: '{cont[0].text.strip()[:40]}'")
        driver.execute_script("arguments[0].click();", cont[0])
        time.sleep(3)
        print(f"  after continue: {driver.current_url[:80]}")
    else:
        print("  no continue btn")

    print("\n== DONE — observed only ==")

if __name__ == "__main__":
    main()
