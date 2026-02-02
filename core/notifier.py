import urllib.request

def ntfy_send(base_url, topic, message, title="MEI", priority="3", tags=""):
    url = f"{base_url.rstrip('/')}/{topic}"
    headers = {
        "Title": title,
        "Priority": priority,
        "Tags": tags,
        "Markdown": "yes"
    }
    
    req = urllib.request.Request(url, data=message.encode("utf-8"), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            status = resp.status
            print(f"[notifier] Success! ntfy response: {status}")
            return status
    except Exception as e:
        print(f"[notifier] CRITICAL FAILURE: {e}")
        return None