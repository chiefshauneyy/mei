import subprocess
from datetime import datetime

def run_agent(agent_name: str) -> str:
    print(f"[MEI] Executing: {agent_name}")
    try:
        # We now redirect stderr to stdout so we catch crashes too
        result = subprocess.run(
            ["python3", "-m", f"agents.{agent_name}.run"],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        output = result.stdout.strip()
        error = result.stderr.strip()

        if result.returncode != 0:
            return f"### ❌ {agent_name} Crashed\n```\n{error}\n```"
        
        return output if output else f"### ⚪ {agent_name}\nNo data returned."
        
    except Exception as e:
        return f"### ⚠️ {agent_name} Runner Error\n{str(e)}"

def run_all(agent_names: list[str]) -> str:
    reports = []
    for a in agent_names:
        report = run_agent(a)
        if report:
            reports.append(report)
    
    # If everything is empty, we still want a message so you know MEI is alive
    if not reports:
        return "### 🤖 MEI System Check\nAll agents returned empty strings."
        
    return "\n\n---\n\n".join(reports)