#!/usr/bin/env python3
"""Click a bookable (green) button on the finder and dump what opens.
Observes ONLY — never submits payment / never completes a booking.
"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from booking_helper import _find_local_driver, _detect_chrome_version

PORT = os.environ.get("REAL_CHROME_PORT", "9222")
URL = os.environ.get("DIAG_URL", "https://www.goethe.de/ins/de/en/prf/ort/ham/gzb1.cfm")
BUTTON_TEXT = os.environ.get("DIAG_BUTTON", "Select modules")

def norm(t):
    return " ".join((t or "").lower().split())

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
    print(f"Attached. URL now: {driver.current_url[:90]}")

    print(f"Loading {URL} ...")
    driver.get(URL)
    time.sleep(5)
    print(f"Title: {driver.title}")

    # ── All ENABLED buttons matching book/select/buchen ──
    btns = driver.find_elements(By.XPATH,
        "//*[self::a or self::button][not(@disabled)]"
        "[contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'book')"
        " or contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'select')"
        " or contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'buchen')"
        " or contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'module')]")
    print(f"\nBookable (enabled) buttons found: {len(btns)}")
    target = None
    for b in btns:
        try:
            txt = (b.text or "").strip()[:60]
            cls = b.get_attribute("class") or ""
            href = b.get_attribute("href") or ""
            print(f"  <{b.tag_name}> '{txt}' class='{cls[:45]}' href='{href[:80]}'")
            if target is None and norm(BUTTON_TEXT) in norm(txt):
                target = b
        except Exception:
            pass
    if target is None and btns:
        target = btns[0]  # fallback: first bookable
    if target is None:
        print("  (no bookable button — booking not open)")
        return

    print(f"\nClicking: '{target.text.strip()[:40]}' ...")
    try:
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", target)
        time.sleep(1)
        driver.execute_script("arguments[0].click();", target)
    except Exception as e:
        print(f"Click failed: {e}")
        return

    time.sleep(4)

    # ── What happened? ──
    print(f"\nURL after click: {driver.current_url[:150]}")
    print(f"Title after click: {driver.title}")

    # new tab/window? (booking often opens a new tab)
    wins = driver.window_handles
    print(f"Window handles: {len(wins)}")
    if len(wins) > 1:
        driver.switch_to.window(wins[-1])
        time.sleep(3)
        print(f"Switched to new tab URL: {driver.current_url[:150]}")
        print(f"New tab title: {driver.title}")

    # modal / dialog
    modals = driver.find_elements(By.CSS_SELECTOR, ".modal, .modal-dialog, [class*='modal'], [role='dialog'], [class*='popup'], [class*='drawer']")
    print(f"\nModal/dialog elements: {len(modals)}")
    for m in modals[:5]:
        try:
            txt = (m.text or "").strip()[:500].replace("\n", " | ")
            if txt:
                print(f"  MODAL: {txt}")
        except Exception:
            pass

    # buttons on the resulting page
    newbtns = driver.find_elements(By.XPATH,
        "//*[self::a or self::button][not(@disabled)]")
    shown = 0
    for b in newbtns:
        try:
            t = (b.text or "").strip()[:50]
            if t:
                print(f"  BTN: '{t}'")
                shown += 1
                if shown >= 12:
                    break
        except Exception:
            pass

    # body preview around 'module' / 'weiter' / 'next'
    body = driver.find_element(By.TAG_NAME, "body").text
    for kw in ["module", "weiter", "next", "prüfungsteil", "exam part"]:
        idx = body.lower().find(kw)
        if idx >= 0:
            print(f"\nBODY[{kw}]: ...{body[max(0,idx-60):idx+140]}...".replace("\n", " "))
            break

    print("\n== DONE — observed only, nothing was submitted ==")

if __name__ == "__main__":
    main()
