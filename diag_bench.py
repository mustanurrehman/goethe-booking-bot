#!/usr/bin/env python3
"""One-shot fast benchmark of the coe flow REACHING the CAS login, using the
bot's real handlers. Stops at the login page (observe only — no creds)."""
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
    lg = bh.setup_logger("diag_bench")
    T = time.monotonic()

    driver.get(URL); time.sleep(6)
    print(f"[{(time.monotonic()-T):.0f}s] loaded exam page")

    btn = bh.find_book_buttons(driver)
    if not btn:
        print("no book button"); return
    target = bh.pick_preferred_button(btn, "Hamburg") or btn[0]
    print(f"[{(time.monotonic()-T):.0f}s] clicking '{target.text.strip()[:30]}'")
    bh.human_move_and_click(driver, target)
    time.sleep(4)

    ok = bh._handle_coe_options_modules(driver, {}, lg)
    print(f"[{(time.monotonic()-T):.0f}s] coe/options handled={ok} URL={driver.current_url[:50]}")
    time.sleep(2.5)

    ok2 = bh._handle_coe_selection_gate(driver, {}, lg)
    print(f"[{(time.monotonic()-T):.0f}s] coe/selection handled={ok2} URL={driver.current_url[:70]}")
    time.sleep(3.5)

    print(f"\n== TOTAL {time.monotonic()-T:.0f}s to CAS login: {driver.current_url[:70]} ==")

if __name__ == "__main__":
    main()
