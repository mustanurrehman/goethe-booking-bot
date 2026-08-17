"""Fetch A1/A2/B1 pages and find booking buttons using requests."""
import re, json
import urllib.request
from bs4 import BeautifulSoup

urls = {
    "A1": "https://www.goethe.de/ins/pk/en/spr/prf/gzsd1.cfm",
    "A2": "https://www.goethe.de/ins/pk/en/spr/prf/gzsd2.cfm",
    "B1": "https://www.goethe.de/ins/pk/en/spr/prf/gzb1.cfm",
}

for level, url in urls.items():
    print(f"\n{'='*50}")
    print(f"  {level}: {url}")
    print('='*50)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode()
        soup = BeautifulSoup(html, 'html.parser')
        buttons = soup.find_all('button', class_=re.compile(r'\bstandard\b'))
        print(f"  Found {len(buttons)} standard button(s):")
        for btn in buttons:
            classes = btn.get('class', [])
            disabled = btn.get('disabled')
            text = btn.get_text(strip=True)[:80]
            print(f"    classes={classes}")
            print(f"    disabled={bool(disabled)}")
            print(f"    text='{text}'")
            print(f"    outer HTML: {str(btn)[:250]}")
            print()
        if not buttons:
            # Try finding any button with "select" or "bookable" text
            all_btns = soup.find_all('button')
            print(f"  No standard buttons. Found {len(all_btns)} total buttons:")
            for btn in all_btns[:5]:
                text = btn.get_text(strip=True)[:60]
                cls = btn.get('class', [])
                print(f"    class={cls} text='{text}'")
    except Exception as e:
        print(f"  ERROR: {e}")
