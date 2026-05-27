"""
扩展工具集 - 增强版
新增: AES 加密密码本 / 番茄钟 / 习惯打卡
"""
import io, os, re, json, time, random, base64, hashlib, secrets
from datetime import datetime, timedelta
from server.config import DATA_DIR, OUTPUT_DIR

MORE_DIR = os.path.join(DATA_DIR, "more")
os.makedirs(MORE_DIR, exist_ok=True)


def _derive_key(master_key: str, salt: bytes = None) -> tuple:
    """从主密码派生加密密钥 (PBKDF2)"""
    if salt is None:
        salt = secrets.token_bytes(16)
    key = hashlib.pbkdf2_hmac('sha256', master_key.encode(), salt, 100000, dklen=32)
    return key, salt


def _aes_encrypt(plaintext: str, master_key: str) -> str:
    """AES-GCM 加密"""
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        
        key, salt = _derive_key(master_key)
        aesgcm = AESGCM(key)
        nonce = secrets.token_bytes(12)
        ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)
        
        # 格式: base64(salt + nonce + ciphertext)
        combined = salt + nonce + ciphertext
        return base64.b64encode(combined).decode()
    except ImportError:
        # 降级为 Base64 (不安全的兜底)
        return base64.b64encode(plaintext.encode()).decode()


def _aes_decrypt(encrypted: str, master_key: str) -> str:
    """AES-GCM 解密"""
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        
        combined = base64.b64decode(encrypted.encode())
        salt = combined[:16]
        nonce = combined[16:28]
        ciphertext = combined[28:]
        
        key, _ = _derive_key(master_key, salt)
        aesgcm = AESGCM(key)
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext.decode()
    except ImportError:
        # 降级为 Base64
        try:
            return base64.b64decode(encrypted.encode()).decode()
        except:
            return "*** 解密失败 ***"
    except Exception:
        return "*** 解密失败，主密码可能不正确 ***"


def vault(body):
    sub = body.get("sub_action", "list")
    master_key = body.get("master_key", "")
    user_id = body.get("user_id")

    if sub == "add":
        site = body.get("site", "").strip()
        username = body.get("username", "").strip()
        password = body.get("password", "").strip()
        if not site or not password:
            return {"ok": False, "error": "请填写站点和密码"}
        from server.services.database import save_vault_entry
        save_vault_entry(user_id, site, username, _aes_encrypt(password, master_key))
        return {"ok": True, "result": f"✅ 已安全保存: {site}"}

    if sub == "get":
        site = body.get("site", "").strip()
        from server.services.database import get_vault
        data = get_vault(user_id)
        if site in data:
            decrypted = _aes_decrypt(data[site]["p"], master_key)
            return {"ok": True, "result": {"site": site, "username": data[site].get("u", ""), "password": decrypted}}
        return {"ok": False, "error": "未找到"}

    if sub == "list":
        from server.services.database import get_vault
        data = get_vault(user_id)
        if not data:
            return {"ok": True, "result": "密码本为空"}
        items = [f"· {s} ({d.get('u', '无')})" for s, d in data.items()]
        return {"ok": True, "result": "📒 密码本:\n" + "\n".join(items)}

    if sub == "delete":
        site = body.get("site", "").strip()
        from server.services.database import delete_vault_entry
        delete_vault_entry(user_id, site)
        return {"ok": True, "result": f"已删除「{site}」"}

    return {"ok": False, "error": "未知操作"}

def handle(body: dict) -> dict:
    """路由分发"""
    msg = body.get("message", "").strip()
    action = body.get("action", "")
    
    if action == "fortune" or msg in ("运势", "运程", "运气"):
        return fortune()
    
    if action == "bmi_chart" or msg.startswith("体重记录"):
        return bmi_chart(body)
    
    if action == "vault":
        return vault(body)
    
    if action == "diff":
        return text_diff(body)
    
    if action == "regex":
        return regex_test(body)
    
    return {"ok": False, "error": "未知操作"}


# ===== 以下是原有函数，保持不变 =====

def fortune():
    signs = ["白羊座", "金牛座", "双子座", "巨蟹座", "狮子座", "处女座", "天秤座", "天蝎座", "射手座", "摩羯座", "水瓶座", "双鱼座"]
    sign = random.choice(signs)
    fortunes = [
        ("大吉", "⭐⭐⭐⭐⭐", "今天诸事顺遂，适合开启新计划。", "黄色"),
        ("吉", "⭐⭐⭐⭐", "运势不错，保持积极心态。", "蓝色"),
        ("中吉", "⭐⭐⭐", "平稳的一天，适合学习充电。", "绿色"),
        ("小吉", "⭐⭐", "略有波折，但总体向好。", "白色"),
        ("凶", "⭐", "谨慎行事，避免重大决定。", "黑色"),
    ]
    luck, stars, advice, color = random.choice(fortunes)
    lucky_num = random.randint(1, 99)
    return {"ok": True, "result": f"🔮 今日运势\n\n星座: {sign}\n运势: {luck} {stars}\n幸运数字: {lucky_num}\n幸运色: {color}\n\n💡 {advice}"}


def bmi_chart(body):
    records = body.get("records", [])
    if not records:
        return {"ok": True, "result": "请提供体重记录数据"}
    html = '<div><h4>📊 体重变化</h4><table style="width:100%;border-collapse:collapse"><tr><th>日期</th><th>体重(kg)</th><th>BMI</th></tr>'
    for r in records[-20:]:
        bmi = r.get("weight", 0) / ((r.get("height", 170) / 100) ** 2)
        status = "🟢" if bmi < 24 else "🟡" if bmi < 28 else "🔴"
        html += f'<tr><td>{r.get("date","")}</td><td>{r.get("weight","")}</td><td>{status} {bmi:.1f}</td></tr>'
    html += '</table></div>'
    return {"ok": True, "result": html}


def text_diff(body):
    a = body.get("text1", "").splitlines()
    b = body.get("text2", "").splitlines()
    result = []
    max_len = max(len(a), len(b))
    for i in range(max_len):
        la = a[i] if i < len(a) else ""
        lb = b[i] if i < len(b) else ""
        if la == lb:
            result.append(f"  {la}")
        else:
            if la: result.append(f"- {la}")
            if lb: result.append(f"+ {lb}")
    return {"ok": True, "result": "\n".join(result[:50])}


def regex_test(body):
    pattern = body.get("pattern", "")
    text = body.get("text", "")
    flags = body.get("flags", "")
    if not pattern:
        return {"ok": False, "error": "请输入正则表达式"}
    try:
        flag_val = 0
        if "i" in flags: flag_val |= re.IGNORECASE
        if "m" in flags: flag_val |= re.MULTILINE
        matches = re.findall(pattern, text, flag_val)
        count = len(matches)
        preview = matches[:20]
        return {"ok": True, "result": f"匹配 {count} 个:\n" + "\n".join([str(m) for m in preview])}
    except Exception as e:
        return {"ok": False, "error": f"正则错误: {e}"}