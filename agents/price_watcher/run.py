import re, time, random
from datetime import datetime
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth 
from core.config import load_config
from core.state import get_conn, init_db

def fetch_stealth(url: str) -> str:
    try:
        with sync_playwright() as p:
            # We add a common window size and disable the automation flag
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                java_script_enabled=True
            )
            page = context.new_page()
            stealth(page)

            # Warm up by visiting Google first (looks like an organic referral)
            page.goto("https://www.google.com")
            time.sleep(random.uniform(1, 2))
            
            # Now go to the target
            page.goto(url, wait_until="networkidle", timeout=60000)
            
            # Wait for price elements (specific to MPB's slow JS)
            page.wait_for_timeout(5000)
            
            # Simple scroll
            page.mouse.wheel(0, 400)
            time.sleep(2)
            
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