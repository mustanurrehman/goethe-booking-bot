#!/usr/bin/env python3
"""Diagnose the coe /coe/psp-selection payment step WITHOUT booking.
Runs the fixed _fill_step_payment selection logic, clicks Continue ONLY if
we are on the payment step, then dumps the resulting page. Stops before any
final confirm/submit/payment button is clicked (review page is observed only).
"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import booking_helper as bh
from booking_helper import _find_local_driver, _detect_chrome_version

PORT = os.environ.get("REAL_CHROME_PORT", "9222")


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
    print(f"Attached. URL now: {driver.current_url[:120]}")

    # If we are not on a payment step, report where we are and stop.
    cur = driver.current_url
    if "psp-selection" not in cur and "payment" not in cur.lower():
        body = driver.find_element(By.TAG_NAME, "body").text[:300]
        print(f"Not on payment step. URL: {cur[:120]}")
        print(f"BODY: {norm(body)[:250]}")
        print("Re-enter flow manually to reach /coe/psp-selection, then re-run.")
        return

    # ── Inspect radios BEFORE fixing ──
    radios = driver.find_elements(By.CSS_SELECTOR, "input[type='radio']")
    print(f"\nPayment radios found: {len(radios)}")
    for i, r in enumerate(radios):
        try:
            label = driver.execute_script(
                "var l=arguments[0].closest('label');"
                "return (l? l.textContent : arguments[0].parentElement.textContent)||''", r)
            print(f"  radio[{i}] label='{' '.join((label or '').split())[:60]}' "
                  f"checked={r.is_selected()} displayed={r.is_displayed()} enabled={r.is_enabled()}")
        except Exception as e:
            print(f"  radio[{i}] inspect failed: {e}")

    # ── Run the FIXED payment fill (selects radio, clicks Continue) ──
    student = {}
    lg = bh.setup_logger("diag_payment")
    result = bh._fill_step_payment(driver, student, lg)

    time.sleep(2)
    print(f"\n_fill_step_payment returned: {result}")
    print(f"URL after: {driver.current_url[:150]}")

    # ── Which radio is selected now? ──
    radios2 = driver.find_elements(By.CSS_SELECTOR, "input[type='radio']")
    for i, r in enumerate(radios2):
        try:
            if r.is_selected():
                label = driver.execute_script(
                    "var l=arguments[0].closest('label');"
                    "return (l? l.textContent : arguments[0].parentElement.textContent)||''", r)
                print(f"  SELECTED radio[{i}]: '{' '.join((label or '').split())[:60]}'")
        except Exception:
            pass

    # ── Error message / validation? ──
    body = driver.find_element(By.TAG_NAME, "body").text
    low = body.lower()
    for kw in ["please select a method", "method of payment", "error", "beachten", "required"]:
        idx = low.find(kw)
        if idx >= 0:
            print(f"\nBODY[{kw}]: ...{norm(body[max(0, idx-40):idx+160])}...")

    # ── If advanced to a review step, OBSERVE ONLY (do NOT click confirm) ──
    print(f"\nTitle: {driver.title}")
    print("== DONE — observed only, final confirm NOT clicked ==")


if __name__ == "__main__":
    main()
