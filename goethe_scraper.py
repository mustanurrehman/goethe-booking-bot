"""Scrape Pakistan exam schedule from Goethe API per level (A1, A2, B1).

Uses Exam Finder API directly with ScrapingBee for live fetching.
Cache TTL: 1 hour. Falls back to Playwright -> curl_cffi -> cached data.
"""
from __future__ import annotations

import json
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import requests

SCRAPINGBEE_API_KEY = os.environ.get("SCRAPINGBEE_API_KEY", "")

try:
    from curl_cffi import requests as curl_requests
    HAS_CURL = True
except Exception:
    HAS_CURL = False

CACHE_TTL = 3600

PK_LEVEL_URLS: Dict[str, str] = {
    "A1": "https://www.goethe.de/ins/pk/en/spr/prf/gzsd1.cfm",
    "A2": "https://www.goethe.de/ins/pk/en/spr/prf/gzsd2.cfm",
    "B1": "https://www.goethe.de/ins/pk/en/spr/prf/gzb1.cfm",
}

PK_CATEGORY_CODES: Dict[str, str] = {
    "A1": "E004",
    "A2": "E005",
    "B1": "E006",
}

PK_INSTITUTE_IDS = ["O%2010000366"]

EXAM_API_URL = "https://www.goethe.de/rest/examfinder/exams/institute/" + ",".join(PK_INSTITUTE_IDS)

CITY_MAP = {
    "karachi": "Karachi",
    "lahore": "Lahore",
    "islamabad": "Islamabad",
}


@dataclass
class ExamEntry:
    level: str
    city: str
    exam_date: str
    reg_open: str
    reg_open_time: str = ""
    exam_end_date: str = ""
    price_full: str = ""
    price_reduced: str = ""
    url: str = ""
    button_link: str = ""


SCRAPER_DIR = Path(__file__).parent.absolute()

_last_cache: dict = {"data": None, "ts": 0}
_scraping_in_progress = threading.Event()


def _load_fallback_data() -> List[ExamEntry]:
    entries: List[ExamEntry] = []
    fp = SCRAPER_DIR / "pk_fallback.json"
    if not fp.exists():
        return entries
    try:
        data = json.loads(fp.read_text(encoding="utf-8"))
        for exam in data.get("DATA", []):
            level = exam.get("languageLevel", "").strip()
            if level not in ("A1", "A2", "B1"):
                continue
            loc = (exam.get("locationName") or "").strip()
            city = _map_city(loc)
            start_date = (exam.get("startDate") or "").strip()
            end_date = (exam.get("endDate") or "").strip()
            book_from = (exam.get("bookFrom") or "").strip()
            book_time = (exam.get("bookFromTimeFormatted") or "").strip()
            price = (exam.get("price") or "").strip()
            btn_link = (exam.get("buttonLink") or "").strip()

            if not start_date:
                continue
            date_str = start_date
            if end_date and end_date != start_date:
                date_str = f"{start_date} - {end_date}"

            entries.append(ExamEntry(
                level=level,
                city=city or loc,
                exam_date=date_str,
                reg_open=book_from,
                reg_open_time=book_time,
                exam_end_date=end_date,
                price_full=price,
                url=PK_LEVEL_URLS.get(level, ""),
                button_link=btn_link,
            ))
    except Exception as e:
        print(f"[pk_scraper] Fallback load error: {e}")
    return entries


def _save_to_fallback(data: dict):
    try:
        fp = SCRAPER_DIR / "pk_fallback.json"
        fp.write_text(json.dumps(data, indent=2), encoding="utf-8")
        print(f"[pk_scraper] Saved fallback ({data.get('RECORDCOUNT', 0)} entries)")
    except Exception as e:
        print(f"[pk_scraper] Fallback save error: {e}")


def get_schedule(force_refresh: bool = False) -> List[ExamEntry]:
    now = time.time()
    if not force_refresh and _last_cache["data"] and (now - _last_cache["ts"]) < CACHE_TTL:
        return _last_cache["data"]

    if force_refresh:
        _refresh_sync()
        return _last_cache["data"] or _load_fallback_data()

    if not _scraping_in_progress.is_set():
        _scraping_in_progress.set()
        t = threading.Thread(target=_refresh_in_background, daemon=True)
        t.start()

    return _last_cache["data"] if _last_cache["data"] else _load_fallback_data()


def _refresh_sync():
    all_entries: List[ExamEntry] = []
    levels = ("A1", "A2", "B1")
    with ThreadPoolExecutor(max_workers=len(levels)) as exe:
        fut = {exe.submit(_scrape_level, lv): lv for lv in levels}
        for f in as_completed(fut):
            lv = fut[f]
            try:
                entries = f.result()
                print(f"[pk_scraper] {lv}: {len(entries)} exams")
                all_entries.extend(entries)
            except Exception as e:
                print(f"[pk_scraper] Error scraping {lv}: {e}")
    if all_entries:
        _last_cache["data"] = all_entries
        _last_cache["ts"] = time.time()
        print(f"[pk_scraper] Sync refresh: {len(all_entries)} entries")
    else:
        print(f"[pk_scraper] Sync refresh got 0 entries")


def _refresh_in_background():
    try:
        all_entries: List[ExamEntry] = []
        for level in ("A1", "A2", "B1"):
            try:
                entries = _scrape_level(level)
                print(f"[pk_scraper] {level}: {len(entries)} exams")
                all_entries.extend(entries)
            except Exception as e:
                print(f"[pk_scraper] Error scraping {level}: {e}")
            time.sleep(2)
        if all_entries:
            _last_cache["data"] = all_entries
            _last_cache["ts"] = time.time()
            print(f"[pk_scraper] Refresh complete: {len(all_entries)} entries")
        else:
            print(f"[pk_scraper] Refresh got 0 entries, keeping cache")
    except Exception as e:
        print(f"[pk_scraper] Background refresh error: {e}")
    finally:
        _scraping_in_progress.clear()


def _scrape_level(level: str) -> List[ExamEntry]:
    category = PK_CATEGORY_CODES.get(level, "")
    if not category:
        return []
    url = PK_LEVEL_URLS.get(level, "")
    params = {
        "sortField": "startDate",
        "hasJUGroup": "true",
        "dataMode": "0",
        "langId": "1",
        "langIsoCodes": "en",
        "countryIsoCode": "pk",
        "count": "50",
        "start": "1",
        "hasERGroup": "true",
        "isODP": "0",
        "category": category,
        "type": "ER",
        "timezone": "47",
        "sortOrder": "ASC",
    }

    if SCRAPINGBEE_API_KEY:
        entries = _scrape_via_scrapingbee(level, url, params)
        if entries:
            return entries

    if HAS_CURL:
        entries = _scrape_via_curl_cffi(level, url, params)
        if entries:
            return entries

    try:
        from playwright.sync_api import sync_playwright
        entries = _scrape_with_pw(level, url)
        if entries:
            return entries
    except ImportError:
        pass
    except Exception as e:
        print(f"[pk_scraper] Playwright error for {level}: {e}")

    return entries


def _scrape_via_scrapingbee(level: str, url: str, params: dict) -> List[ExamEntry]:
    import urllib.parse
    try:
        target_url = f"{EXAM_API_URL}?{urllib.parse.urlencode(params)}"
        encoded = urllib.parse.quote(target_url, safe='')
        bee_url = (f"https://app.scrapingbee.com/api/v1"
                    f"?api_key={SCRAPINGBEE_API_KEY}"
                    f"&url={encoded}"
                    f"&render_js=false"
                    f"&premium_proxy=true")
        print(f"[pk_scraper] ScrapingBee request for {level}...")
        resp = requests.get(bee_url, timeout=60)
        if resp.status_code == 200:
            try:
                data = resp.json()
                if isinstance(data, dict) and data.get("SUCCESS"):
                    entries = _parse_api_response(data, level, url)
                    if entries:
                        _save_to_fallback(data)
                        print(f"[pk_scraper] ScrapingBee {level}: {len(entries)} entries")
                        return entries
                else:
                    print(f"[pk_scraper] ScrapingBee {level}: unexpected response shape")
            except json.JSONDecodeError as je:
                print(f"[pk_scraper] ScrapingBee {level} not JSON: {je}")
        else:
            print(f"[pk_scraper] ScrapingBee {level} HTTP {resp.status_code}: {resp.text[:200]}")
    except Exception as e:
        print(f"[pk_scraper] ScrapingBee error for {level}: {e}")
    return []


def _scrape_via_curl_cffi(level: str, url: str, params: dict) -> List[ExamEntry]:
    try:
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": url,
            "Origin": "https://www.goethe.de",
            "DNT": "1",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
        }
        # Retry with verify=False when the local CA chain is broken (common on
        # dev machines / home networks). Railway keeps a valid chain, so we try
        # verified TLS first and only relax it on an SSL failure.
        last_exc = None
        resp = None
        for verify in (True, False):
            try:
                resp = curl_requests.get(
                    EXAM_API_URL,
                    params=params,
                    headers=headers,
                    impersonate="chrome131",
                    timeout=30,
                    verify=verify,
                )
                break
            except Exception as exc:
                last_exc = exc
                if "certificate" in str(exc).lower() or "ssl" in str(exc).lower():
                    print(f"[pk_scraper] curl_cffi {level} SSL verify error, retrying without verification: {exc}")
                    continue
                raise
        if resp is None:
            raise last_exc or RuntimeError("curl_cffi request failed")
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, dict) and data.get("SUCCESS"):
                entries = _parse_api_response(data, level, url)
                if entries:
                    _save_to_fallback(data)
                    print(f"[pk_scraper] curl_cffi {level}: {len(entries)} entries")
                    return entries
    except Exception as e:
        print(f"[pk_scraper] curl_cffi error for {level}: {e}")
    return []


def _scrape_with_pw(level: str, url: str) -> List[ExamEntry]:
    from playwright.sync_api import sync_playwright
    entries: List[ExamEntry] = []
    api_responses: List[dict] = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/149.0.0.0 Safari/537.36",
            locale="en-PK",
        )
        page = ctx.new_page()

        def on_response(resp):
            if resp.status == 200 and "/rest/examfinderv3/exams" in resp.url:
                try:
                    body = resp.json()
                    if isinstance(body, dict) and body.get("SUCCESS"):
                        api_responses.append(body)
                except Exception:
                    pass

        page.on("response", on_response)
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(5000)
        browser.close()

    if api_responses:
        data = api_responses[0]
        entries = _parse_api_response(data, level, url)
        if entries:
            _save_to_fallback(data)
    return entries


def _parse_api_response(data: dict, level: str, url: str) -> List[ExamEntry]:
    entries: List[ExamEntry] = []
    seen: set = set()
    for exam in data.get("DATA", []):
        loc = (exam.get("locationName") or "").strip()
        city = _map_city(loc)
        start_date = (exam.get("startDate") or "").strip()
        end_date = (exam.get("endDate") or "").strip()
        book_from = (exam.get("bookFrom") or "").strip()
        book_time = (exam.get("bookFromTimeFormatted") or "").strip()
        price = (exam.get("price") or "").strip()
        btn_link = (exam.get("buttonLink") or "").strip()

        if not start_date:
            continue

        date_str = start_date
        if end_date and end_date != start_date:
            date_str = f"{start_date} - {end_date}"

        dedup_key = f"{city}|{date_str}|{btn_link}"
        if dedup_key in seen:
            continue
        seen.add(dedup_key)

        entries.append(ExamEntry(
            level=level,
            city=city or loc,
            exam_date=date_str,
            reg_open=book_from,
            reg_open_time=book_time,
            exam_end_date=end_date,
            price_full=price,
            url=url,
            button_link=btn_link,
        ))
    return entries


def _map_city(location: str) -> str:
    loc_lower = location.lower()
    for key, val in CITY_MAP.items():
        if key in loc_lower:
            return val
    return location


def classify_dates(entries: List[ExamEntry]) -> dict:
    """Classify entries into past and coming dates."""
    now = datetime.now()
    past: List[ExamEntry] = []
    coming: List[ExamEntry] = []
    for e in entries:
        try:
            parts = e.exam_date.split(" - ")[0].split(".")
            d = datetime(int(parts[2]), int(parts[1]), int(parts[0]))
            if d < now:
                past.append(e)
            else:
                coming.append(e)
        except (IndexError, ValueError):
            coming.append(e)
    return {"past": past, "coming": coming, "all": entries}


def to_dict(entries: List[ExamEntry]) -> List[Dict]:
    return [asdict(e) for e in entries]
