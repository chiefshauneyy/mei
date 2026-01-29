from core.config import load_config
from core.runner import run_all
from core.state import get_conn, init_db

# Phase 1: simple fixed list; later read from config.
AGENTS = ["daily_briefing"]

def main() -> None:
    cfg = load_config()
    conn = get_conn(cfg["paths"]["db"])
    init_db(conn)
    conn.close()

    rc = run_all(AGENTS)
    raise SystemExit(rc)

if __name__ == "__main__":
    main()
