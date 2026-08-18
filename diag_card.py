#!/usr/bin/env python3
"""Full-flow to payment: select CREDIT CARD radio (never PayPal). Observed."""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import booking_helper as bh

PORT = os.environ.get("REAL_CHROME_PORT", "9222")
URL = "https://www.goethe.de/ins/de/en/prf/ort/ham/gzb1.cfm"

def main():
    driver_path = bh._find_local_driver(bh._detect_chrome_version())
    if not driver_path: print("FAIL no driver"); return
    opts = Options(); opts.add_experimental_option("debuggerAddress", f"127.0.0.1:{PORT}")
    svc = Service(driver_path)
    if os.name == "nt": svc.creation_flags = 0
    driver = webdriver.Chrome(service=svc, options=opts)
    lg = bh.setup_logger("diag_card")
    T = time.monotonic()

    # Real student data (config.csv, gitignored)
    students = bh.load_all_students(os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.csv"))
    st = students[0]
    print(f"[{(time.monotonic()-T):.0f}s] student: {st.get('name')}")

    driver.get(URL); time.sleep(6)
    print(f"[{(time.monotonic()-T):.0f}s] page loaded: {driver.current_url[:60]}")
    btn = bh.find_book_buttons(driver)
    if not btn:
        print("no book button — booking not open"); return
    target = bh.pick_preferred_button(btn, "Hamburg") or btn[0]
    print(f"[{(time.monotonic()-T):.0f}s] click '{target.text.strip()[:30]}'")
    bh.human_move_and_click(driver, target); time.sleep(4)

    bh._handle_coe_options_modules(driver, st, lg); time.sleep(2.5)
    bh._handle_coe_selection_gate(driver, st, lg); time.sleep(4)
    print(f"[{(time.monotonic()-T):.0f}s] after gate: {driver.current_url[:60]}")

    # Follow through login -> oska-acc -> voucher -> psp-selection
    # Uses real student data, but NEVER the final confirm.
    for step in range(10):
        time.sleep(2.5)
        u = driver.current_url
        print(f"[{(time.monotonic()-T):.0f}s] step{step} url: {u[:60]}")
        if "psp-selection" in u:
            break
        if "login.goethe.de" in u:
            print("   (login page — waiting for SSO auto-redirect)")
            continue
        if "oska-acc" in u:
            bh._fill_step_personal_data_1(driver, st, lg)
        if "wicket" in u and "oska" not in u:
            bh._fill_step_personal_data_2(driver, st, lg)
    print("\n== final url:", driver.current_url[:80], "==")
    driver.quit()

if __name__ == "__main__":
    main()
