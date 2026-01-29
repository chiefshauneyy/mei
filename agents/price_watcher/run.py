from __future__ import annotations

import re
import subprocess
from datetime import datetime

from core.config import load_config
from core.notifier import ntfy_send
from core.state import get_conn, init_db


def fetch_text_curl(url: str) -> str:
    return subprocess.check_output(
        [
            "curl", "-L", "-s", "--compressed",
            "-H", "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "-H", "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "-H", "Accept-Language: en-US,en;q=0.9",
            url,
        ],
        text=True,
    )


def fetch_text_playwright(url: str) -> str:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page.goto(url, wait_until="networkidle", timeout=60000)
        html = page.content()
        browser.close()
        return html


def looks_like_js_shell(html: str) -> bool:
    # MPB returns a small JS shell via curl; rendered page is much larger.
    return len(html) < 50000


def fetch_text(url: str) -> str:
    html = fetch_text_curl(url)
    if looks_like_js_shell(html):
        html = fetch_text_playwright(url)
    return html


def parse_min_price(text: str, regex: str, min_price: float | None = None) -> float | None:
    matches = re.findall(regex, text)
    if not matches:
        return None

    prices: list[float] = []
    for m in matches:
        raw = m.replace(",", "").strip()
        try:
            val = float(raw)
        except ValueError:
            continue

        if min_price is not None and val < min_price:
            continue

        prices.append(val)

    return min(prices) if prices else None



def should_alert(old: float | None, new: float, drop_percent: float | None, drop_absolute: float | None) -> bool:
    if old is None:
        return False
    if drop_absolute is not None and (old - new) >= drop_absolute:
        return True
    if drop_percent is not None and new <= old * (1.0 - (drop_percent / 100.0)):
        return True
    return False


def upsert_item(conn, name: str, url: str, price: float | None, currency: str | None) -> float | None:
    now = datetime.now().isoformat(timespec="seconds")

    row = conn.execute(
        "SELECT last_price FROM price_watch WHERE name=? AND url=?",
        (name, url),
    ).fetchone()
    old = row[0] if row else None

    if row:
        conn.execute(
            "UPDATE price_watch SET last_price=?, currency=?, updated_at=? WHERE name=? AND url=?",
            (price, currency, now, name, url),
        )
    else:
        conn.execute(
            "INSERT INTO price_watch (name, url, last_price, currency, updated_at) VALUES (?, ?, ?, ?, ?)",
            (name, url, price, currency, now),
        )

    conn.commit()
    return old


def main() -> None:
    cfg = load_config()
    pw = cfg.get("price_watch", {})
    if not pw.get("enabled", True):
        print("[price_watcher] disabled")
        return

    items = pw.get("items", [])
    if not items:
        print("[price_watcher] no items configured (config.price_watch.items is empty)")
        return

    base_url = cfg["ntfy"]["base_url"]
    topic = cfg["ntfy"]["topics"]["alerts"]
    db_path = cfg["paths"]["db"]

    conn = get_conn(db_path)
    init_db(conn)

    default_regex = r"\$\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{2})?)"
    alerted = 0

    for it in items:
        name = it.get("name", "Unnamed item")
        url = it["url"]
        currency = it.get("currency", "USD")
        regex = it.get("regex", default_regex)
        drop_percent = it.get("drop_percent")
        drop_absolute = it.get("drop_absolute")

        try:
            text = fetch_text(url)
            min_price = it.get("min_price")
            new_price = parse_min_price(text, regex, min_price=min_price)

        except Exception as e:
            print(f"[price_watcher] fetch failed: {name} -> {e}")
            continue

        if new_price is None:
            print(f"[price_watcher] price not found: {name}")
            upsert_item(conn, name, url, None, currency)
            continue

        old_price = upsert_item(conn, name, url, new_price, currency)

        if should_alert(old_price, new_price, drop_percent, drop_absolute):
            drop_amt = (old_price - new_price) if old_price is not None else 0
            drop_pct = ((drop_amt / old_price) * 100.0) if old_price else 0
            msg = "\n".join(
                [
                    f"{name}",
                    f"Old: {old_price:.2f} {currency}" if old_price is not None else "Old: (unknown)",
                    f"New: {new_price:.2f} {currency}",
                    f"Drop: {drop_amt:.2f} ({drop_pct:.1f}%)",
                    "",
                    url,
                ]
            )
            ntfy_send(
                base_url=base_url,
                topic=topic,
                message=msg,
                title="MEI Alert: Price Drop",
                priority="4",
                tags="money_with_wings,rotating_light",
            )
            alerted += 1
            print(f"[price_watcher] ALERT: {name}")
        else:
            print(f"[price_watcher] ok: {name} @ {new_price:.2f} {currency}")

    conn.close()
    print(f"[price_watcher] done (alerts sent: {alerted})")


if __name__ == "__main__":
    main()
