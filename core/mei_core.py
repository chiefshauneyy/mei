import os

from core.config import load_config
from core.runner import run_all
from core.state import get_conn, init_db

DAILY_AGENTS = ["daily_briefing"]
HOURLY_AGENTS = ["price_watcher"]

def main() -> None:
    cfg = load_config()

    conn = get_conn(cfg["paths"]["db"])
    init_db(conn)
    conn.close()

    mode = os.getenv("MEI_MODE", "daily").strip().lower()
    agents = DAILY_AGENTS if mode == "daily" else HOURLY_AGENTS

    rc = run_all(agents)
    raise SystemExit(rc)

if __name__ == "__main__":
    main()
