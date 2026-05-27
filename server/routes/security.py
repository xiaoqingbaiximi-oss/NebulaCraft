import re
import base64
import hashlib
import json as jmod

def handle(body):
    a = body.get("action", "password_strength")
    t = body.get("text", "")

    if a == "password_strength":
        s = (len(t) >= 8) + (len(t) >= 12) + bool(re.search(r'[A-Z]', t)) + bool(re.search(r'[a-z]', t)) + bool(re.search(r'\d', t)) + bool(re.search(r'[!@#$%^&*]', t))
        return {"ok": True, "score": s, "level": ["非常弱", "弱", "一般", "强", "非常强", "极强"][min(s, 5)]}

    if a == "base64_encode":
        return {"ok": True, "result": base64.b64encode(t.encode()).decode()}

    if a == "base64_decode":
        try:
            return {"ok": True, "result": base64.b64decode(t.encode()).decode()}
        except:
            return {"ok": False, "error": "无效 Base64"}

    if a == "md5":
        return {"ok": True, "result": hashlib.md5(t.encode()).hexdigest()}

    if a == "sha256":
        return {"ok": True, "result": hashlib.sha256(t.encode()).hexdigest()}

    if a == "jwt_decode":
        try:
            parts = t.split(".")
            if len(parts) != 3:
                return {"ok": False, "error": "无效 JWT"}
            payload = base64.b64decode(parts[1] + "==").decode()
            return {"ok": True, "result": jmod.loads(payload)}
        except:
            return {"ok": False, "error": "解析失败"}

    return {"ok": False, "error": f"不支持: {a}"}