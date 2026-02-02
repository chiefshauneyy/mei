import re, time, random, os
from datetime import datetime
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth 
from core.config import load_config
from core.state import get_conn, init_db

def fetch_stealth(url: str) -> str:
    # Create a temporary user data dir to store 'cookies' and look real
    user_data_dir = os.path.join(os.getcwd(), "data", "browser_profile")
    
    try:
        with sync_playwright() as p:
            # We launch with headless=False just to test. 
            # If this works on your Mac, we've found the 'tell'.
            browser = p.chromium.launch_persistent_context(
                user_data_dir,
                headless=True, # Try True first with the persistent context
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--start-maximized'
                ],
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
            )
            
            page = browser.pages[0] if browser.pages else browser.new_page()
            stealth(page)

            # Visit Google first
            page.goto("https://www.google.com", wait_until="networkidle")
            time.sleep(random.uniform(2, 4))
            
            # Go to MPB
            response = page.goto(url, wait_until="networkidle", timeout=90000)
            
            # If we hit a Cloudflare 'Waiting' room, wait longer
            if "Just a moment" in page.content():
                print("[price_watcher] Cloudflare detected, waiting 10s...")
                time.sleep(10)
            
            # Scroll like a human
            page.mouse.wheel(0, random.randint(300, 700))
            time.sleep(3)
            
            content = page.content()
            browser.close()
            return content
    except Exception as e:
        return f"ERROR: {str(e)}"

# ... rest of main() stays the same as previous version ...

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