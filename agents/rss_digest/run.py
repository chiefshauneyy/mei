from __future__ import annotations

import hashlib
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime

from core.config import load_config
from core.notifier import ntfy_send
from core.state import get_conn, init_db


def _hash_key(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]


def fetch_xml(url: str) -> str:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "MEI/1.0 (+local)"},
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = resp.read()
    return data.decode("utf-8", errors="ignore")


def parse_feed(xml_text: str) -> tuple[str, list[dict]]:
    """
    Returns (feed_title, entries)
    entry keys: id, title, link, published
    Supports RSS 2.0 and Atom.
    """
    root = ET.fromstring(xml_text.strip())

    # Atom: <feed xmlns="http://www.w3.org/2005/Atom">
    if root.tag.endswith("feed"):
        ns = ""
        if root.tag.startswith("{") and "}" in root.tag:
            ns = root.tag.split("}")[0] + "}"
        title_el = root.find(f"{ns}title")
        feed_title = (title_el.text or "").strip() if title_el is not None else "Atom Feed"

        entries = []
        for e in root.findall(f"{ns}entry"):
            eid = (e.findtext(f"{ns}id") or "").strip()
            etitle = (e.findtext(f"{ns}title") or "").strip()

            link = ""
            for link_el in e.findall(f"{ns}link"):
                rel = (link_el.attrib.get("rel") or "alternate").strip()
                href = (link_el.attrib.get("href") or "").strip()
                if rel == "alternate" and href:
                    link = href
                    break
            if not link:
                link = (e.findtext(f"{ns}link") or "").strip()

            published = (e.findtext(f"{ns}updated") or e.findtext(f"{ns}published") or "").strip()
            if not eid:
                eid = f"{etitle}|{link}"
            entries.append({"id": eid, "title": etitle, "link": link, "published": published})
        return feed_title, entries

    # RSS 2.0: <rss><channel>...
    channel = root.find("channel")
    if channel is None:
        return "Unknown Feed", []

    feed_title = (channel.findtext("title") or "RSS Feed").strip()
    entries = []
    for item in channel.findall("item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        guid = (item.findtext("guid") or "").strip()
        pub = (item.findtext("pubDate") or "").strip()

        eid = guid or f"{title}|{link}"
        entries.append({"id": eid, "title": title, "link": link, "published": pub})
    return feed_title, entries


def kv_get(conn, key: str) -> str | None:
    row = conn.execute("SELECT v FROM kv WHERE k=?", (key,)).fetchone()
    return row[0] if row else None


def kv_set(conn, key: str, val: str) -> None:
    now = datetime.now().isoformat(timespec="seconds")
    conn.execute(
        "INSERT INTO kv(k,v,updated_at) VALUES(?,?,?) "
        "ON CONFLICT(k) DO UPDATE SET v=excluded.v, updated_at=excluded.updated_at",
        (key, val, now),
    )
    conn.commit()


def main() -> None:
    cfg = load_config()
    dig = cfg.get("rss_digest", {})
    if not dig.get("enabled", True):
        print("[rss_digest] disabled")
        return

    feeds = dig.get("feeds", [])
    if not feeds:
        print("[rss_digest] no feeds configured (config.rss_digest.feeds is empty)")
        return

    per_run_max = int(dig.get("max_items", 3))
    per_feed_max = int(dig.get("max_per_feed", 2))

    base_url = cfg["ntfy"]["base_url"]
    topic = cfg["ntfy"]["topics"]["digest"]
    db_path = cfg["paths"]["db"]

    conn = get_conn(db_path)
    init_db(conn)

    new_items: list[str] = []
    total_new = 0

    for f in feeds:
        name = f.get("name", "Feed")
        url = f["url"]
        state_key = f"rss_last::{_hash_key(url)}"
        last_id = kv_get(conn, state_key)

        try:
            xml_text = fetch_xml(url)
            feed_title, entries = parse_feed(xml_text)
        except Exception as e:
            print(f"[rss_digest] fetch/parse failed: {name} -> {e}")
            continue

        # newest-first heuristic: many feeds already order this way
        entries = entries[:50]

        fresh = []
        for ent in entries:
            if last_id and ent["id"] == last_id:
                break
            fresh.append(ent)

        if not fresh:
            continue

        # Keep only a small number per feed
        fresh = fresh[:per_feed_max]
        total_new += len(fresh)

        for ent in fresh:
            title = ent["title"] or "(untitled)"
            link = ent["link"]
            new_items.append(f"- {name}: {title}\n  {link}")

        # Update state to the newest item id in the feed
        kv_set(conn, state_key, entries[0]["id"])

    conn.close()

    if not new_items:
        print("[rss_digest] no new items")
        return

    # Cap overall message size
    new_items = new_items[:per_run_max]
    msg = "\n".join(
        [
            f"New items: {len(new_items)} (of {total_new} found)",
            "",
            *new_items,
        ]
    )

    ntfy_send(
        base_url=base_url,
        topic=topic,
        message=msg,
        title="MEI Digest",
        priority="3",
        tags="newspaper,scroll",
    )

    print(f"[rss_digest] sent ({len(new_items)} items)")


if __name__ == "__main__":
    main()
