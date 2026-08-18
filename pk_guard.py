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

            # Backend seat probe (best-effort): the /rest API carries capacityMax /
            # capacityOptimal per exam (0 while not yet bookable). curl_cffi gets
            # 403 on this IP, but fetch() from the page's own origin works (it
            # reuses the browser session/Akamai cookie). We evaluate it in-page.
            api_extra = {}
            try:
                seat_js = r"""
                var out = {};
                (async function(){
                  try {
                    var u='https://www.goethe.de/rest/examfinder/exams/institute/O%2010000366?category=E006&type=ER&countryIsoCode=pk&locationName=&count=10&start=1&langId=1&timezone=47&isODP=0&sortField=startDate&sortOrder=ASC&dataMode=0&langIsoCodes=en';
                    var r = await fetch(u,{credentials:'include'});
                    var j = await r.json();
                    var arr = j.DATA || j.data || [];
                    var rows=[];
                    for (var i=0;i<arr.length;i++){
                      var e=arr[i]; if(!e) continue;
                      rows.push({loc:e.locationName||'?', start:e.startDate||'', end:e.endDate||'',
                                 bookFrom:e.bookFrom||'', capacityMax:e.capacityMax, capacityOptimal:e.capacityOptimal,
                                 availability:e.availability, price:e.price});
                    }
                    out.n=arr.length; out.rows=rows;
                  } catch(e){ out.err=String(e); }
                  window.__guard_seats=out;
                })()
                """
                driver.execute_script(seat_js)
                time.sleep(2.5)
                sj = driver.execute_script("return window.__guard_seats")
                if sj and sj.get("rows") is not None:
                    rows = sj.get("rows", [])
                    cap_min = None; cap_max = None
                    for rw in rows:
                        try:
                            c = rw.get("capacityMax")
                            if isinstance(c, (int, float)) and c > 0:
                                if cap_min is None or c < cap_min: cap_min = c
                                if cap_max is None or c > cap_max: cap_max = c
                        except Exception:
                            pass
                    api_extra = {
                        "browser_api_exams": sj.get("n", 0),
                        "browser_api_bookFrom": rows[0].get("bookFrom") if rows else None,
                        "api_seats_row_max": cap_max,
                        "api_seats_row_min": cap_min,
                        "browser_api_rows": rows[:4],
                    }
                    print(f"[guard] browser API: exams={api_extra['browser_api_exams']} "
                          f"bookFrom={api_extra['browser_api_bookFrom']} capMax={cap_max}")
            except Exception as api_exc:
                print(f"[guard] browser API seat probe skipped: {str(api_exc)[:80]}")

            btn = find_book_buttons(driver)
            if btn:
                # FALSE-POSITIVE GUARD: the shared debug Chrome can be left on a
                # NON-Pakistan finder (e.g. our own Germany probes) by another
                # session, and find_book_buttons would happily return a Hamburg
                # "SELECT MODULES" button. A real Pakistan bookable slot must
                # show a Pakistan location in its row. If the current page is
                # not the Pakistan B1 finder, reload it before trusting anything.
                row_now = button_row_text(btn[0]).lower()
                if "karachi" not in row_now and "lahore" not in row_now and "islamabad" not in row_now and "/pk/" not in driver.current_url:
                    print(f"[guard] page not Pakistan finder (row='{row_now[:60]}') — reloading PK page")
                    driver.get(URL_PK)
                    time.sleep(6)
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
                # Which city is this bookable slot for? Target is Lahore; a live
                # SELECT MODULES on the Karachi row is the TEST slot, Lahore is
                # the FINAL booking.
                row_low = row.lower()
                if "karachi" in row_low:
                    payload["slot_city"] = "Karachi"
                elif "lahore" in row_low:
                    payload["slot_city"] = "Lahore"
                elif "islamabad" in row_low:
                    payload["slot_city"] = "Islamabad"
                else:
                    payload["slot_city"] = row_low[:40]
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