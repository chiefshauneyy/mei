from datetime import datetime
import platform
import subprocess

from core.config import load_config
from core.notifier import ntfy_send


def get_uptime() -> str:
    # macOS: "uptime" is reliable
    try:
        out = subprocess.check_output(["uptime"], text=True).strip()
        return out
    except Exception:
        return "uptime unavailable"


def main() -> None:
    cfg = load_config()
    base_url = cfg["ntfy"]["base_url"]
    topic = cfg["ntfy"]["topics"]["daily"]

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    host = platform.node() or "macbook"
    os_name = f"{platform.system()} {platform.release()}"

    msg = "\n".join([
        f"Time: {now}",
        f"Host: {host}",
        f"OS: {os_name}",
        f"Uptime: {get_uptime()}",
        "",
        "Status: MEI online ✅",
    ])

    ntfy_send(
        base_url=base_url,
        topic=topic,
        message=msg,
        title="MEI Daily",
        priority="3",
        tags="robot,calendar",
    )

    print("[daily_briefing] sent v2")


if __name__ == "__main__":
    main()
