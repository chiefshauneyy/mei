import os
import sys
# This ensures the root directory is always in the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.config import load_config
from core.runner import run_all
from core.notifier import ntfy_send

def main():
    cfg = load_config()
    mode = os.getenv("MEI_MODE", "hourly").strip().lower()
    
    if mode == "daily":
        agents = ["weather_alert", "rss_digest", "price_watcher"]
        topic = cfg["ntfy"]["topics"]["daily"]
    else:
        agents = ["price_watcher", "rss_digest"]
        topic = cfg["ntfy"]["topics"]["digest"]

    report_content = run_all(agents)
    
    ntfy_send(
        base_url=cfg["ntfy"]["base_url"],
        topic=topic,
        message=report_content,
        title=f"MEI {mode.capitalize()} Report"
    )

if __name__ == "__main__":
    main()