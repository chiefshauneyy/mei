import re, time, random, os
from datetime import datetime
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth 
from core.config import load_config
from core.state import get_conn, init_db

def fetch_stealth(url: str) -> str:
    chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    user_data_dir = os.path.join(os.getcwd(), "data", "browser_profile")
    
    try:
        with sync_playwright() as p:
            # TEMP CHANGE: Set headless=False so you can see the window
            browser = p.chromium.launch_persistent_context(
                user_data_dir,
                executable_path=chrome_path, 
                headless=False, 
                args=['--disable-blink-features=AutomationControlled']
            )
            
            page = browser.pages[0]
            stealth(page)

            print(f"[price_watcher] Navigating to {url}...")
            page.goto(url, wait_until="networkidle", timeout=90000)
            
            # If you see a "Verify you are human" box on your screen, CLICK IT manually.
            # We will wait 20 seconds here to give you time to act.
            print("[price_watcher] Waiting for manual interaction/page load...")
            time.sleep(20) 
            
            # Wait for the price to appear
            page.wait_for_selector("span[data-testid='price']", timeout=15000)
            
            content = page.content()
            browser.close()
            return content
    except Exception as e:
        return f"ERROR: {str(e)}"

# ... main function remains the same ...

def main() -> str:
    cfg = load_config()
    items = cfg.get("price_watch", {}).get("items", [])
    conn = get_conn(cfg["paths"]["db"])
    init_db(conn)
    
    reports = []
    for it in items:
        html = fetch_stealth(it["url"])
        
        # Check if we got the actual page content
        if "ERROR" in html or "Access Denied" in html:
            reports.append(f"**{it['name']}**: 🛡️ Security block or timeout.")
            continue

        # Regex tuned for MPB's specific price format
        match = re.search(r"\$([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{2})?)", html)
        if match:
            new_price = float(match.group(1).replace(",", ""))
            reports.append(f"**{it['name']}**: **${new_price:,.2f}**")
            conn.execute("INSERT INTO price_watch (name, url, last_price, updated_at) VALUES (?,?,?,?) "
                         "ON CONFLICT(url) DO UPDATE SET last_price=excluded.last_price", 
                         (it['name'], it['url'], new_price, datetime.now().isoformat()))
        else:
            reports.append(f"**{it['name']}**: 🔍 Price not found.")

    conn.commit()
    conn.close()
    return "### 💰 Price Watcher\n" + "\n".join(reports) if reports else ""

if __name__ == "__main__":
    print(main().strip())