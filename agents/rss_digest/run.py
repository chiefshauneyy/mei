from __future__ import annotations
import hashlib
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from core.config import load_config
from core.state import get_conn, init_db

def _hash_key(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]

def fetch_xml(url: str) -> str:
    # A more convincing browser header
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/xml, text/xml, */*"
    }
    req = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read().decode("utf-8", errors="ignore")

def parse_feed(xml_text: str) -> tuple[str, list[dict]]:
    root = ET.fromstring(xml_text.strip())
    # Atom Support
    if root.tag.endswith("feed"):
        ns = root.tag.split("}")[0] + "}" if "}" in root.tag else ""
        entries = []
        for e in root.findall(f"{ns}entry")[:10]:
            title = (e.findtext(f"{ns}title") or "No Title").strip()
            link = e.find(f"{ns}link").attrib.get("href") if e.find(f"{ns}link") is not None else ""
            entries.append({"id": e.findtext(f"{ns}id") or link, "title": title, "link": link})
        return root.findtext(f"{ns}title") or "Feed", entries
    # RSS 2.0 Support
    channel = root.find("channel")
    if channel is not None:
        entries = []
        for item in channel.findall("item")[:10]:
            title = (item.findtext("title") or "No Title").strip()
            link = (item.findtext("link") or "").strip()
            entries.append({"id": item.findtext("guid") or link, "title": title, "link": link})
        return channel.findtext("title") or "Feed", entries
    return "Unknown", []

def main() -> str:
    cfg = load_config()
    dig = cfg.get("rss_digest", {})
    if not dig.get("enabled", True): return ""
    
    conn = get_conn(cfg["paths"]["db"])
    init_db(conn)
    
    reports = []
    for f in dig.get("feeds", []):
        try:
            feed_title, entries = parse_feed(fetch_xml(f["url"]))
            state_key = f"rss_last::{_hash_key(f['url'])}"
            last_id = conn.execute("SELECT v FROM kv WHERE k=?", (state_key,)).fetchone()
            
            fresh = [e for e in entries if not last_id or e["id"] != last_id[0]][:int(dig.get("max_per_feed", 1))]
            if fresh:
                for e in fresh:
                    reports.append(f"**{f.get('name', feed_title)}**: [{e['title']}]({e['link']})")
                conn.execute("INSERT INTO kv(k,v,updated_at) VALUES(?,?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v", 
                             (state_key, entries[0]["id"], datetime.now().isoformat()))
        except Exception as e:
            print(f"Feed error {f.get('name')}: {e}")
    
    conn.commit()
    conn.close()
    
    if not reports: return "### 📰 RSS Digest\nNo new items."
    return "### 📰 RSS Digest\n" + "\n".join(reports[:int(dig.get("max_items", 5))])

if __name__ == "__main__":
    print(main())