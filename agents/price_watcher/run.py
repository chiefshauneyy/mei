import re
import time
import random
from datetime import datetime
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth 
from core.config import load_config
from core.state import get_conn, init_db

def fetch_stealth(url: str) -> str:
    # Use a single context manager for the entire browser session
    try:
        with sync_playwright() as p:
            # handle_sigint=False is required for running in subprocesses on macOS
            browser = p.chromium.launch(
                headless=True, 
                slow_mo=random.randint(50, 200),
                args=['--disable-blink-features=AutomationControlled']
            )
            
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                viewport={'width': 1280, 'height': 720}
            )
            page = context.new_page()
            stealth(page)
            
            # Realistic human-like navigation
            time.sleep(random.uniform(1, 3))
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_load_state("networkidle")
            
            # Trigger lazy loaders
            page.mouse.wheel(0, 500)
            time.sleep(2)
            
            content = page.content()
            browser.close()
            return content
    except Exception as e:
        return f"ERROR: {str(e)}"

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
        
        if "ERROR" in html or "Forbidden" in html or "🛡️" in html:
            reports.append(f"**{name}**: 🛡️ Security block or timeout.")
            continue

        # More flexible regex to handle different currency formats and comma separators
        match = re.search(r"[\$\£\€]\s?([0-9,]+(?:\.[0-9]{2})?)", html)
        if match:
            raw_price = match.group(1).replace(",", "")
            new_price = float(raw_price)
            reports.append(f"**{name}**: **${new_price:,.2f}**")
            
            conn.execute("INSERT INTO price_watch (name, url, last_price, updated_at) VALUES (?,?,?,?) "
                         "ON CONFLICT(url) DO UPDATE SET last_price=excluded.last_price", 
                         (name, it["url"], new_price, datetime.now().isoformat()))
        else:
            reports.append(f"**{name}**: 🔍 Price not found.")

    conn.commit()
    conn.close()
    
    if not reports: return ""
    return "### 💰 Price Watcher\n" + "\n".join(reports)

if __name__ == "__main__":
    # We strip the output to ensure no extra whitespace messes with the runner
    print(main().strip())