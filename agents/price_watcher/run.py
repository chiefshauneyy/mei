import re
import time
import random
from datetime import datetime
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
from core.config import load_config
from core.state import get_conn, init_db

def fetch_stealth(url: str) -> str:
    with sync_playwright() as p:
        # Launching with a specific 'slow_mo' to beat timing-based bot checks
        browser = p.chromium.launch(headless=True, slow_mo=random.randint(50, 200))
        
        # Emulating a real MacBook screen
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 720}
        )
        page = context.new_page()
        stealth_sync(page)
        
        try:
            # Human-like delay before navigating
            time.sleep(random.uniform(1, 3))
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            
            # Wait for the price elements to actually render
            page.wait_for_load_state("networkidle")
            
            # Scroll down slightly to trigger lazy-loading (very human behavior)
            page.mouse.wheel(0, 500)
            time.sleep(2)
            
            return page.content()
        except Exception as e:
            return f"ERROR: {e}"
        finally:
            browser.close()

def main() -> str:
    cfg = load_config()
    pw_cfg = cfg.get("price_watch", {})
    if not pw_cfg.get("enabled", True): return ""
    
    items = pw_cfg.get("items", [])
    conn = get_conn(cfg["paths"]["db"])
    init_db(conn)
    
    reports = []
    for it in items:
        name = it.get("name", "Item")
        html = fetch_stealth(it["url"])
        
        if "ERROR" in html or "Forbidden" in html:
            reports.append(f"**{name}**: 🛡️ Blocked by site security.")
            continue

        # Using a broader regex to catch prices regardless of exact HTML structure
        match = re.search(r"[\$\£\€]\s?([0-9,]+\.[0-9]{2})", html)
        if match:
            new_price = float(match.group(1).replace(",", ""))
            reports.append(f"**{name}**: **${new_price:,.2f}**")
            # DB update logic
            conn.execute("INSERT INTO price_watch (name, url, last_price, updated_at) VALUES (?,?,?,?) "
                         "ON CONFLICT(url) DO UPDATE SET last_price=excluded.last_price", 
                         (name, it["url"], new_price, datetime.now().isoformat()))
        else:
            reports.append(f"**{name}**: 🔍 Could not locate price.")

    conn.commit()
    conn.close()
    return "### 💰 Price Watcher\n" + "\n".join(reports) if reports else ""

if __name__ == "__main__":
    print(main())