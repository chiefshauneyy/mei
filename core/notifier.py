import urllib.request

def ntfy_send(base_url: str, topic: str, message: str, title: str = "MEI", priority: str = "3", tags: str = "robot") -> None:
    url = f"{base_url.rstrip('/')}/{topic}"
    req = urllib.request.Request(
        url,
        data=message.encode("utf-8"),
        headers={"Title": title, "Priority": priority, "Tags": tags},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10):
        pass
