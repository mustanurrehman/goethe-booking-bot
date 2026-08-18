#!/usr/bin/env python3
"""Attach to real Chrome (port 9222) and dump the exam-page structure:
iframes, pr_finder container, and any bookable buttons inside them.
"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from booking_helper import _find_local_driver, _detect_chrome_version

PORT = os.environ.get("REAL_CHROME_PORT", "9222")
DEFAULT_URL = "https://www.goethe.de/ins/pk/en/spr/prf/gzb1.cfm"

def main():
    # Allow a URL argument to inspect any country's page, e.g.:
    #   python diag_page.py https://www.goethe.de/ins/in/en/spr/prf/gzb1.cfm
    url = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1].startswith("http") else DEFAULT_URL
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
    print(f"Attached to Chrome on port {PORT}, current URL: {driver.current_url}")

    print(f"Loading {url} ...")
    driver.get(url)
    time.sleep(5)
    print(f"Title: {driver.title}")
    print(f"Final URL: {driver.current_url}")

    # ── iframes on the page ──
    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    print(f"\n== IFRAMES: {len(iframes)} ==")
    for i, fr in enumerate(iframes):
        try:
            print(f"  [{i}] id={fr.get_attribute('id')} src={(fr.get_attribute('src') or '')[:120]} class={fr.get_attribute('class')}")
        except Exception as e:
            print(f"  [{i}] error: {e}")

    # ── pr_finder container presence (outer doc) ──
    print("\n== OUTER-DOC finder/table/search ==")
    for sel in ["#pr_finder_9523459", ".pr-finder", "[class*='finder']", "table", ".standard"]:
        els = driver.find_elements(By.CSS_SELECTOR, sel)
        print(f"  {sel}: {len(els)}")

    # ── Dump the finder container's own HTML so we can see the real structure ──
    print("\n== FINDER CONTAINER HTML (first 6000 chars) ==")
    dumped_html = ""
    for sel in ["[class*='pr_finder']", "[id*='pr_finder']", "[class*='finder']"]:
        els = driver.find_elements(By.CSS_SELECTOR, sel)
        for el in els[:2]:
            try:
                h = el.get_attribute("outerHTML") or ""
                dumped_html += h
            except Exception:
                pass
    print(dumped_html[:6000] if dumped_html else "(no finder container HTML found)")

    # ── All <a>/<button> inside the finder region, printed with class+href+text ──
    print("\n== FINDER-REGION links/buttons ==")
    printed = 0
    for sel in ["[class*='pr_finder']", "[id*='pr_finder']", "[class*='finder']"]:
        els = driver.find_elements(By.CSS_SELECTOR, sel)
        for el in els[:2]:
            try:
                nodes = el.find_elements(By.XPATH, ".//*[self::a or self::button]")
                for n in nodes[:40]:
                    try:
                        cls = n.get_attribute("class") or ""
                        href = n.get_attribute("href") or ""
                        txt = (n.text or "").strip()[:60]
                        if not (txt or href or cls):
                            continue
                        print(f"  <{n.tag_name}> txt='{txt}' class='{cls[:50]}' href='{href[:100]}'")
                        printed += 1
                    except Exception:
                        pass
            except Exception:
                pass
    if not printed:
        print("  (no <a>/<button> found in finder region)")

    # ── If any iframe, drill into the first few ──
    for i, fr in enumerate(iframes[:3]):
        try:
            driver.switch_to.frame(fr)
            body = driver.find_element(By.TAG_NAME, "body").text[:600]
            print(f"\n== INSIDE IFRAME [{i}]: {driver.current_url[:80]} ==")
            print(f"  body: {body}")
            btns = driver.find_elements(By.XPATH,
                "//*[self::a or self::button][contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'book')"
                " or contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'select')"
                " or contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'buchen')]")
            for b in btns[:15]:
                try:
                    cls = b.get_attribute("class") or ""
                    if "disabled" in cls.lower():
                        continue
                    print(f"    <{b.tag_name}> '{b.text[:50].strip()}' class='{cls[:40]}'")
                except Exception:
                    pass
            driver.switch_to.parent_frame()
        except Exception as e:
            print(f"  IFRAME [{i}] error: {e}")
            try:
                driver.switch_to.parent_frame()
            except Exception:
                pass

    driver.switch_to.default_content()
    print("\n== DONE (same browser window — don't close Chrome) ==")

if __name__ == "__main__":
    main()