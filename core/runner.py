import subprocess
from datetime import datetime

def run_agent(agent_name: str) -> int:
    print(f"[MEI] Running agent: {agent_name}")
    # Run agent as a module so imports work
    return subprocess.run(
        ["python3", "-m", f"agents.{agent_name}.run"]
    ).returncode

def run_all(agent_names: list[str]) -> int:
    print(f"[MEI] Tick @ {datetime.now().isoformat(timespec='seconds')}")
    failures = 0
    for a in agent_names:
        if run_agent(a) != 0:
            failures += 1
    return 0 if failures == 0 else 1
