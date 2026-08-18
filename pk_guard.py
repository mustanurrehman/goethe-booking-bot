#!/usr/bin/env python3
"""Standing guard: poll the PAKISTAN B1 finder for a bookable SELECT MODULES
button. When one appears, notify + write a small STATE file that the bot can
pick up. Runs against the real Chrome (debug port). No booking is ever
submitted — this only detects availability.
"""
import sys, os, time, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from booking_helper import (_find_local_driver, _detect_chrome_version, find_book_buttons,
                            button_row_text, normalize_text, check_slot_via_api)
from booking_helper import setup_logger

PORT = os.environ.get("REAL_CHROME_PORT", "9222")
URL_PK = "https://www.goethe.de/ins/pk/en/spr/prf/gzb1.cfm"
STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pk_guard_state.json")
POLL = int(os.environ.get("PK_GUARD_POLL", "180"))  # seconds between checks
RESTART_CHROME_HINT = "START_DEBUG_CHROME_BAT"
_API_LOGGER = setup_logger("pk_guard_api")  # needs a logger; reuse a dedicated one


def norm(t):
    return " ".join((t or "").lower().split())


def write_state(payload: dict) -> None:
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
    except Exception:
        pass


def main() -> int:
    print(f"[guard] Pakistan B1 watch started (poll {POLL}s). Ctrl+C to stop.")
    last_cycle = None
    while True:
        driver = None
        try:
            if last_cycle is None or time.monotonic() - last_cycle >= POLL:
                last_cycle = time.monotonic()
            driver_path = _find_local_driver(_detect_chrome_version())
            if not driver_path:
                print("[guard] no cached chromedriver"); time.sleep(POLL); continue
            opts = Options()
            opts.add_experimental_option("debuggerAddress", f"127.0.0.1:{PORT}")
            svc = Service(driver_path)
            if os.name == "nt":
                svc.creation_flags = 0
            driver = webdriver.Chrome(service=svc, options=opts)
            driver.set_page_load_timeout(25)
            driver.get(URL_PK)
            time.sleep(6)

            body = driver.find_element(By.TAG_NAME, "body").text
            low = norm(body)

            # Backend seat probe (best-effort): the /rest API may carry per-exam
            # capacity fields. If it answers, surface the count. Never blocks the
            # watch when the API is blocked or silent (it frequently 403s).
            api_extra = {}
            try:
                api = check_slot_via_api("B1", _API_LOGGER)
                if api.get("api_ok"):
                    api_extra = {
                        "api_seats_total": api.get("total_seats_shown"),
                        "api_seats_row_min": api.get("min_seat_count"),
                        "api_seats_row_max": api.get("max_seat_count"),
                        "api_seats_rows": api.get("seats")[:6] if api.get("seats") else [],
                    }
                    print(f"[guard] API: seats_row={api_extra['api_seats_row_min']}/{api_extra['api_seats_row_max']} total={api_extra['api_seats_total']}")
            except Exception as api_exc:
                print(f"[guard] API seat probe skipped: {str(api_exc)[:80]}")

            btn = find_book_buttons(driver)
            if not btn:
                # DETAILS reveal (Vue finder)
                try:
                    details = driver.find_elements(By.XPATH,
                        "//*[self::a or self::button][contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'details')]")
                    if details:
                        driver.execute_script("arguments[0].click();", details[0])
                        time.sleep(2)
                    btn = find_book_buttons(driver)
                except Exception:
                    pass

            now = time.strftime("%H:%M:%S")
            if btn:
                row = button_row_text(btn[0])
                print(f"[guard {now}] ** BOOKING OPEN ** button='{btn[0].text.strip()[:40]}' row='{row[:90]}'")
                payload = {
                    "available": True, "time": now, "url": URL_PK,
                    "button_text": btn[0].text.strip()[:60],
                    "row_text": row[:140],
                }
                payload.update(api_extra)
                write_state(payload)
                return 0  # exit; the caller/loop will action the booking
            else:
                hint = ""
                for kw in ["bookable from", "not bookable", "fully booked", "no results", "no exam"]:
                    i = low.find(kw)
                    if i >= 0:
                        hint = f" ({norm(body)[max(0, i-30):i+80]})"
                        break
                print(f"[guard {now}] no bookable button yet{hint}")
                payload = {"available": False, "time": now, "hint": hint.strip()}
                payload.update(api_extra)
                write_state(payload)
        except Exception as exc:
            print(f"[guard] error: {exc}")
            print(f"[guard] {RESTART_CHROME_HINT}")
            write_state({"available": False, "error": str(exc)[:120]})
        finally:
            try:
                if driver:
                    driver.quit()
            except Exception:
                pass
        time.sleep(POLL)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n[guard] stopped.")
        sys.exit(0)