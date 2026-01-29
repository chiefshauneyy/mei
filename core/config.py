import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

def load_config() -> dict:
    cfg_path = BASE_DIR / "config" / "mei.json"
    return json.loads(cfg_path.read_text(encoding="utf-8"))
