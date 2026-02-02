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
            browser = p.chromium.launch_persistent_context(
                user_data_dir,
                executable_path=chrome_path, 
                headless=False, 
                args=['--disable-blink-features=AutomationControlled']
            )
            
            page = browser.pages[0]
            stealth(page)

            print(f"\n[MEI] Navigating to: {url}")
            page.goto(url, wait_until="networkidle", timeout=90000)
            
            # --- THE HOLD ---
            print("\n🚨 ACTION REQUIRED 🚨")
            print("1. Look at the Chrome window that just opened.")
            print("2. Solve any Captcha or 'Verify you are human' boxes.")
            print("3. Once the actual MPB site is visible, come back here.")
            input("👉 Press ENTER in this terminal to continue and save the session...")
            # ----------------
            
            # Wait for price to render
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