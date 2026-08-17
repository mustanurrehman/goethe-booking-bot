#!/usr/bin/env python3
"""
Dump all form fields on the current page for selector debugging.
Run this while on any wizard step during a booking window.
Saves output to form_fields_dump.txt

Usage:
    python scripts/dump_form_fields.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from booking_helper import create_driver, setup_logger

logger = setup_logger("dump_fields")
driver = create_driver(use_headless=False, logger=logger)

try:
    input("Open the wizard page in the browser, then press Enter to dump fields...")

    fields = driver.execute_script("""
        const els = document.querySelectorAll('input, select, textarea, button');
        return Array.from(els).map(el => ({
            tag: el.tagName.toLowerCase(),
            type: el.type || '',
            name: el.name || '',
            id: el.id || '',
            class: el.className || '',
            placeholder: el.placeholder || '',
            label: (() => {
                const label = document.querySelector(`label[for="${el.id}"]`);
                if (label) return label.innerText.trim();
                const parent = el.closest('label');
                if (parent) return parent.innerText.trim();
                const aria = el.getAttribute('aria-label');
                if (aria) return aria;
                return '';
            })(),
            value: el.value || '',
            disabled: el.disabled || false,
            readonly: el.readOnly || false,
            rect: el.getBoundingClientRect().toJSON(),
        }));
    """)

    output = {"url": driver.current_url, "title": driver.title, "fields": fields}
    out_path = Path("form_fields_dump.json")
    out_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"\nDumped {len(fields)} fields to {out_path}")

    print("\n--- Quick Summary ---")
    for f in fields:
        label = f["label"] or f["placeholder"] or f["name"]
        print(f"  {f['tag']:8} name={f['name'][:40]:40} id={f['id'][:40]:40} label={label[:50]}")

finally:
    driver.quit()
