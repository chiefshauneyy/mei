import urllib.request

def ntfy_send(base_url: str, topic: str, message: str, title: str = "MEI", priority: str = "3", tags: str = ""):
    url = f"{base_url}/{topic}"
    headers = {
        "Title": title,
        "Priority": priority,
        "Tags": tags,
        "Markdown": "yes"  # Crucial for headers/links
    }
    
    req = urllib.request.Request(url, data=message.encode("utf-8"), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status
    except Exception as e:
        print(f"[notifier] failed: {e}")
        return None