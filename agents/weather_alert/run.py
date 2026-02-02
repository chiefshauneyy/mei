import json
import urllib.request
from core.config import load_config

def main() -> str:
    cfg = load_config()
    # San Antonio coordinates
    url = "https://api.weather.gov/alerts/active?point=29.4241,-98.4936"
    headers = {"User-Agent": f"(MEI Home Server, {cfg.get('admin_email', 'admin@example.com')})"}

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        
        features = data.get("features", [])
        if not features:
            return "### 🌤 Weather\nNo active alerts for San Antonio."

        alerts = ["### ⚠️ Weather Alerts"]
        for feat in features[:2]:
            p = feat["properties"]
            alerts.append(f"**{p['event']}**\n{p['headline']}")
        return "\n\n".join(alerts)
    except Exception as e:
        return f"### 🌤 Weather\nError fetching alerts: {e}"

if __name__ == "__main__":
    print(main())