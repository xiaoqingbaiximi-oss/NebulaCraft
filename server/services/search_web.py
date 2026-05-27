"""联网搜索服务"""
import re
import urllib.parse
import requests


def search(query, max_results=5):
    results = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    try:
        resp = requests.get(
            f"https://api.duckduckgo.com/?q={urllib.parse.quote(query)}&format=json&no_html=1",
            timeout=10, headers=headers
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("AbstractText"):
                results.append({"title": data.get("AbstractSource", ""), "url": data.get("AbstractURL", ""), "snippet": data.get("AbstractText", "")})
            for r in data.get("Results", [])[:max_results]:
                results.append({"title": r.get("Text", ""), "url": r.get("FirstURL", ""), "snippet": r.get("Text", "")})
    except:
        pass

    if not results:
        try:
            resp = requests.get(f"https://search.bing.com/search?q={urllib.parse.quote(query)}", headers=headers, timeout=10)
            snippets = re.findall(r'<li class="b_algo".*?<h2><a[^>]*>(.*?)</a></h2>.*?<p[^>]*>(.*?)</p>', resp.text, re.DOTALL)
            for s in snippets[:max_results]:
                results.append({"title": re.sub(r"<[^>]+>", "", s[0]), "snippet": re.sub(r"<[^>]+>", "", s[1])})
        except:
            pass

    return results