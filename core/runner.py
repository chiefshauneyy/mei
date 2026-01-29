import subprocess
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

def run_agent(agent_name: str) -> int:
    agent_path = BASE_DIR / "agents" / agent_name / "run.py"
    if not agent_path.exists():
        print(f"[MEI] Missing agent: {agent_name}")
        return 1
    print(f"[MEI] Running agent: {agent_name}")
    return subprocess.run(["python3", str(agent_path)], cwd=str(BASE_DIR)).returncode

def run_all(agent_names: list[str]) -> int:
    print(f"[MEI] Tick @ {datetime.now().isoformat(timespec='seconds')}")
    failures = 0
    for a in agent_names:
        if run_agent(a) != 0:
            failures += 1
    return 0 if failures == 0 else 1
