import os
import urllib.request
from datetime import datetime

TOPIC = os.getenv("NTFY_TOPIC", "mei-alerts")
URL = f"https://ntfy.sh/{TOPIC}"

now = datetime.now().strftime("%Y-%m-%d %H:%M")
message = f"MEI Daily Briefing\nStatus: online\nTime: {now}"

req = urllib.request.Request(
    URL,
    data=message.encode(),
    headers={
        "Title": "MEI",
        "Priority": "3",
        "Tags": "robot",
    },
    method="POST",
)

with urllib.request.urlopen(req, timeout=10):
    pass

print("[daily_briefing] sent")
