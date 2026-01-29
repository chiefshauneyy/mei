from __future__ import annotations

import re
import urllib.request
from datetime import datetime

from core.config import load_config
from core.notifier import ntfy_send
from core.state import get_conn, init_db


def fetch_text(url: str) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X) AppleWebKit/537.36 (KHTML, like Gecko) Chrome Safari"
        },
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = resp.read()
    return data.decode("utf-8", errors="ignore")


def parse_price(text: str, regex: str) -> float | None:
    m = re.search(regex, text)
    if not m:
        return None
    raw = m.group(1).replace(",", "").strip()
    try:
        return float(raw)
    except ValueError:
        return None


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
            new_price = parse_price(text, regex)
        except Exception as e:
            print(f"[price_watcher] fetch failed: {name} -> {e}")
            continue

        if new_price is None:
            print(f"[price_watcher] price not found: {name}")
            old_price = upsert_item(conn, name, url, None, currency)
            continue

        old_price = upsert_item(conn, name, url, new_price, currency)

        if should_alert(old_price, new_price, drop_percent, drop_absolute):
            drop_amt = (old_price - new_price) if old_price is not None else 0
            drop_pct = ((drop_amt / old_price) * 100.0) if old_price else 0
            msg = "\n".join([
                f"{name}",
                f"Old: {old_price:.2f} {currency}" if old_price is not None else "Old: (unknown)",
                f"New: {new_price:.2f} {currency}",
                f"Drop: {drop_amt:.2f} ({drop_pct:.1f}%)",
                "",
                url
            ])
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
