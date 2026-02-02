import os
from core.config import load_config
from core.runner import run_all
from core.notifier import ntfy_send

def main():
    cfg = load_config()
    
    # Determine which agents to run based on the trigger
    mode = os.getenv("MEI_MODE", "hourly").strip().lower()
    
    if mode == "daily":
        # Full morning briefing
        agents = ["weather_alert", "rss_digest", "price_watcher"]
        topic = cfg["ntfy"]["topics"]["daily"]
        title = "☀️ MEI Daily Briefing"
    else:
        # Standard hourly check
        agents = ["price_watcher", "rss_digest"]
        topic = cfg["ntfy"]["topics"]["digest"]
        title = "🤖 MEI Hourly Update"

    # Capture all agent reports into one string
    full_report = run_all(agents)

    if full_report:
        ntfy_send(
            base_url=cfg["ntfy"]["base_url"],
            topic=topic,
            message=full_report,
            title=title,
            priority="3",
            tags="newspaper,cyclone" if mode == "daily" else "gear"
        )
        print(f"[MEI] Sent unified {mode} report to {topic}")
    else:
        print("[MEI] No new data to report.")

if __name__ == "__main__":
    main()