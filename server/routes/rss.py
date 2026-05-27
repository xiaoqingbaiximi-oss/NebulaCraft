"""RSS 订阅"""
import requests
import re


def handle(body):
    url = body.get("url", "").strip()
    if not url:
        return {"ok": False, "error": "请输入RSS地址"}

    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        items = re.findall(r"<item>(.*?)</item>", resp.text, re.DOTALL)
        results = []
        for item in items[:10]:
            title = re.search(r"<title>(.*?)</title>", item)
            link = re.search(r"<link>(.*?)</link>", item)
            desc = re.search(r"<description>(.*?)</description>", item)
            if title:
                results.append({
                    "title": re.sub(r"<[^>]+>", "", title.group(1)),
                    "link": link.group(1).strip() if link else "",
                    "desc": re.sub(r"<[^>]+>", "", desc.group(1))[:200] if desc else "",
                })
        return {"ok": True, "items": results}
    except Exception as e:
        return {"ok": False, "error": str(e)}