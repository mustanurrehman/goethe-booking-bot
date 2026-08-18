#!/usr/bin/env python3
"""From the current CAS login page: login, then walk the coe wizard up to the
payment step and select the CREDIT CARD radio (never PayPal). Observe only —
stops before final confirm. Never books."""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import booking_helper as bh

PORT = os.environ.get("REAL_CHROME_PORT", "9222")


def main():
    driver_path = bh._find_local_driver(bh._detect_chrome_version())
    if not driver_path:
        print("FAIL no driver"); return
    opts = Options(); opts.add_experimental_option("debuggerAddress", f"127.0.0.1:{PORT}")
    svc = Service(driver_path)
    if os.name == "nt": svc.creation_flags = 0
    driver = webdriver.Chrome(service=svc, options=opts)
    lg = bh.setup_logger("diag_card2")
    T = time.monotonic()

    students = bh.load_all_students(os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.csv"))
    st = students[0]

    def where(msg=""):
        print(f"[{(time.monotonic()-T):.0f}s] {msg} URL: {driver.current_url[:70]}")

    where("start")
    u = driver.current_url
    if "login.goethe.de" in u:
        print("Login page — filling credentials from config.csv ...")
        bh._login_attempt(driver, st.get("email",""), st.get("password",""), lg)
        time.sleep(4)
        where("after login")
    else:
        where("(not login page)")

    # Walk through wizard steps by URL.
    # Wicket re-renders the SAME /coe/oska-acc URL for Step1 (Name/Birth) then
    # Step2 (Address) — so on oska-acc we run Step1 once, then Step2.
    step1_done = False
    for i in range(12):
        time.sleep(3)
        u = driver.current_url
        if "psp-selection" in u:
            where(f"step{i}: REACHED payment")
            break
        if "oska-acc" in u and not step1_done:
            where(f"step{i}: personal data 1 (oska-acc)")
            bh._fill_step_personal_data_1(driver, st, lg)
            step1_done = True
        elif "oska-acc" in u:
            where(f"step{i}: personal data 2 (address)")
            bh._fill_step_personal_data_2(driver, st, lg)
        elif "voucher" in u:
            where(f"step{i}: voucher")
            bh._fill_step_promo(driver, st, lg)
        elif "wicket" in u and "oska" not in u:
            where(f"step{i}: address (wicket)")
            bh._fill_step_personal_data_2(driver, st, lg)
        elif "login.goethe.de" in u:
            where(f"step{i}: login again")
            bh._login_attempt(driver, st.get("email",""), st.get("password",""), lg)
        else:
            where(f"step{i}: (other)")

    # On payment step? Select CREDIT CARD
    if "psp-selection" in driver.current_url:
        radios = driver.find_elements(By.CSS_SELECTOR, "input[type='radio']")
        print(f"\nPayment radios: {len(radios)}")
        for r in radios:
            try:
                lab = driver.execute_script(
                    "var l=arguments[0].closest('label');return (l?l.textContent:arguments[0].parentElement.textContent)||''", r)
                print(f"  radio: {' '.join(lab.split())[:40]} checked={r.is_selected()}")
            except Exception:
                pass
        # Apply card rule
        ok = bh._fill_step_payment(driver, st, lg)
        print(f"_fill_step_payment -> {ok}")
        time.sleep(2)
        # Confirm which is selected now
        radios = driver.find_elements(By.CSS_SELECTOR, "input[type='radio']")
        for r in radios:
            try:
                if r.is_selected():
                    lab = driver.execute_script(
                        "var l=arguments[0].closest('label');return (l?l.textContent:arguments[0].parentElement.textContent)||''", r)
                    print(f"SELECTED: {' '.join(lab.split())[:40]}")
            except Exception:
                pass
        print(f"After payment URL: {driver.current_url[:80]}")
    else:
        print(f"\nDid not reach payment. URL: {driver.current_url[:80]}")

    print("\n== DONE observed — final confirm NOT clicked ==")
    driver.quit()


if __name__ == "__main__":
    main()
