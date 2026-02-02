import subprocess
from datetime import datetime

def run_agent(agent_name: str) -> str:
    print(f"[MEI] Running agent: {agent_name}")
    result = subprocess.run(
        ["python3", "-m", f"agents.{agent_name}.run"],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        return result.stdout.strip()
    else:
        return f"### ❌ {agent_name} Failed\nError: {result.stderr.strip()}"

def run_all(agent_names: list[str]) -> str:
    print(f"[MEI] Tick @ {datetime.now().isoformat(timespec='seconds')}")
    reports = []
    for a in agent_names:
        report = run_agent(a)
        if report:
            reports.append(report)
    
    return "\n\n---\n\n".join(reports) # Joins agents with a visual line