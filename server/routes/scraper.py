"""网页剪藏"""
import requests
import re


def handle(body):
    url = body.get("url", "").strip()
    if not url:
        return {"ok": False, "error": "请输入网址"}
    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        text = re.sub(r"<script[^>]*>.*?</script>", "", resp.text, flags=re.DOTALL)
        text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()[:8000]
        title = re.search(r"<title>(.*?)</title>", resp.text, re.I)
        return {"ok": True, "title": title.group(1) if title else url, "text": text}
    except Exception as e:
        return {"ok": False, "error": str(e)}