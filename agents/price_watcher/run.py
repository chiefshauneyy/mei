from __future__ import annotations
import re
import subprocess
from datetime import datetime
from core.config import load_config
from core.state import get_conn, init_db

def fetch_text(url: str) -> str:
    # Try curl first
    try:
        html = subprocess.check_output([
            "curl", "-L", "-s", "--compressed",
            "-H", "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            url
        ], text=True, timeout=15)
        
        # Fallback to Playwright if page is too small (likely JS shell)
        if len(html) < 50000:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url, wait_until="networkidle", timeout=60000)
                html = page.content()
                browser.close()
        return html
    except Exception as e:
        return f"ERROR: {e}"

def main() -> str:
    cfg = load_config()
    pw = cfg.get("price_watch", {})
    if not pw.get("enabled", True): return ""

    conn = get_conn(cfg["paths"]["db"])
    init_db(conn)
    
    reports = []
    items = pw.get("items", [])
    
    for it in items:
        name = it.get("name", "Item")
        url = it["url"]
        regex = it.get("regex", r"\$\s*([0-9,]+(?:\.[0-9]{2})?)")
        
        html = fetch_text(url)
        if "ERROR" in html:
            reports.append(f"**{name}**: Fetch failed.")
            continue

        matches = re.findall(regex, html)
        if not matches:
            reports.append(f"**{name}**: Price not found.")
            continue

        # Clean and find min price
        prices = sorted([float(m.replace(",", "")) for m in matches if m])
        new_price = prices[0]
        
        # Database check for old price
        row = conn.execute("SELECT last_price FROM price_watch WHERE url=?", (url,)).fetchone()
        old_price = row[0] if row else None
        
        # Logic to determine if we show it in the report
        if old_price and new_price < old_price:
            diff = old_price - new_price
            reports.append(f"**{name}**: 📉 **${new_price:.2f}** (Dropped ${diff:.2f}!) [Link]({url})")
        else:
            reports.append(f"**{name}**: ${new_price:.2f} (No change)")

        # Update DB
        conn.execute("INSERT INTO price_watch (name, url, last_price, updated_at) VALUES (?,?,?,?) "
                     "ON CONFLICT(url) DO UPDATE SET last_price=excluded.last_price", 
                     (name, url, new_price, datetime.now().isoformat()))

    conn.commit()
    conn.close()
    
    if not reports: return ""
    return "### 💰 Price Watcher\n" + "\n".join(reports)

if __name__ == "__main__":
    print(main())