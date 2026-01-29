import subprocess
from datetime import datetime
from pathlib import Path

AGENTS = [
    "daily_briefing",
]

BASE_DIR = Path(__file__).resolve().parents[1]

def run_agent(name: str) -> int:
    agent = BASE_DIR / "agents" / name / "run.py"
    if not agent.exists():
        print(f"[MEI] Missing agent: {name}")
        return 1
    return subprocess.run(["python3", str(agent)]).returncode

def main():
    print(f"[MEI] Tick @ {datetime.now().isoformat(timespec='seconds')}")
    failures = 0
    for agent in AGENTS:
        if run_agent(agent) != 0:
            failures += 1
    if failures:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
