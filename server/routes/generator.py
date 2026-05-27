"""
生成器 API - 增强版
支持: 密码 / UUID / 颜色 / 验证码 / 身份 / 假数据 / 随机数 / 占位文本
"""
import random
import string
import uuid
import hashlib
import time


def handle(body):
    gen_type = body.get("type", "password")
    count = min(int(body.get("count", 1)), 20)
    params = body.get("params", {})
    
    generators = {
        "password": _gen_password,
        "uuid": _gen_uuid,
        "color": _gen_color,
        "captcha": _gen_captcha,
        "identity": _gen_identity,
        "lorem": _gen_lorem,
        "random_number": _gen_random_number,
        "hash": _gen_hash,
        "token": _gen_token,
        "username": _gen_username,
        "email": _gen_email,
        "phone": _gen_phone,
        "address": _gen_address,
        "company": _gen_company,
        "credit_card": _gen_credit_card,
    }
    
    gen_func = generators.get(gen_type)
    if not gen_func:
        return {"ok": False, "error": f"不支持的生成类型: {gen_type}"}
    
    results = [gen_func(params) for _ in range(count)]
    
    return {
        "ok": True,
        "type": gen_type,
        "count": count,
        "results": results if count > 1 else results[0],
    }


def _gen_password(params):
    length = min(int(params.get("length", 16)), 128)
    use_upper = params.get("upper", True)
    use_lower = params.get("lower", True)
    use_digits = params.get("digits", True)
    use_symbols = params.get("symbols", True)
    
    chars = ""
    required = []
    
    if use_upper:
        chars += string.ascii_uppercase
        required.append(random.choice(string.ascii_uppercase))
    if use_lower:
        chars += string.ascii_lowercase
        required.append(random.choice(string.ascii_lowercase))
    if use_digits:
        chars += string.digits
        required.append(random.choice(string.digits))
    if use_symbols:
        chars += "!@#$%^&*()_+-=[]{}|;:,.<>?"
        required.append(random.choice("!@#$%^&*()_+-=[]{}|;:,.<>?"))
    
    if not chars:
        chars = string.ascii_letters + string.digits
    
    # 确保包含所有必需字符类型
    password = required + [random.choice(chars) for _ in range(length - len(required))]
    random.shuffle(password)
    
    pwd = "".join(password)
    
    # 密码强度
    strength = _check_strength(pwd)
    
    return {
        "value": pwd,
        "length": len(pwd),
        "strength": strength,
    }


def _check_strength(password):
    score = 0
    if len(password) >= 8: score += 1
    if len(password) >= 12: score += 1
    if len(password) >= 16: score += 1
    if re.search(r'[A-Z]', password): score += 1
    if re.search(r'[a-z]', password): score += 1
    if re.search(r'\d', password): score += 1
    if re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', password): score += 1
    
    levels = ["非常弱", "弱", "一般", "强", "非常强", "极强", "完美"]
    return {
        "score": min(score, 7),
        "level": levels[min(score, 6)],
    }


def _gen_uuid(params):
    ver = params.get("version", 4)
    
    if ver == 1:
        uid = uuid.uuid1()
    elif ver == 3:
        name = params.get("name", "nebulacraft")
        namespace = uuid.NAMESPACE_DNS
        uid = uuid.uuid3(namespace, name)
    elif ver == 5:
        name = params.get("name", "nebulacraft")
        namespace = uuid.NAMESPACE_DNS
        uid = uuid.uuid5(namespace, name)
    else:
        uid = uuid.uuid4()
    
    return {
        "value": str(uid),
        "version": ver,
        "hex": uid.hex,
    }


def _gen_color(params):
    fmt = params.get("format", "hex")
    
    r = random.randint(0, 255)
    g = random.randint(0, 255)
    b = random.randint(0, 255)
    
    hex_str = f"#{r:02x}{g:02x}{b:02x}"
    
    # 颜色名称近似
    color_name = _approximate_color_name(r, g, b)
    
    return {
        "hex": hex_str,
        "rgb": f"rgb({r}, {g}, {b})",
        "hsl": _rgb_to_hsl(r, g, b),
        "name": color_name,
    }


def _approximate_color_name(r, g, b):
    colors = {
        "红色": (255, 0, 0), "绿色": (0, 255, 0), "蓝色": (0, 0, 255),
        "黄色": (255, 255, 0), "青色": (0, 255, 255), "品红": (255, 0, 255),
        "橙色": (255, 165, 0), "紫色": (128, 0, 128), "粉色": (255, 192, 203),
        "棕色": (165, 42, 42), "灰色": (128, 128, 128), "白色": (255, 255, 255),
        "黑色": (0, 0, 0), "海军蓝": (0, 0, 128), "橄榄绿": (128, 128, 0),
    }
    
    min_dist = float("inf")
    closest = "自定义"
    
    for name, (cr, cg, cb) in colors.items():
        dist = (r - cr) ** 2 + (g - cg) ** 2 + (b - cb) ** 2
        if dist < min_dist:
            min_dist = dist
            closest = name
    
    return closest if min_dist < 10000 else "自定义"


def _rgb_to_hsl(r, g, b):
    rn, gn, bn = r / 255, g / 255, b / 255
    mx, mn = max(rn, gn, bn), min(rn, gn, bn)
    l = (mx + mn) / 2
    
    if mx == mn:
        h = s = 0
    else:
        d = mx - mn
        s = d / (2 - mx - mn) if l > 0.5 else d / (mx + mn)
        
        if mx == rn:
            h = ((gn - bn) / d + (6 if gn < bn else 0)) / 6
        elif mx == gn:
            h = ((bn - rn) / d + 2) / 6
        else:
            h = ((rn - gn) / d + 4) / 6
    
    return f"hsl({round(h * 360)}, {round(s * 100)}%, {round(l * 100)}%)"


def _gen_captcha(params):
    length = min(int(params.get("length", 6)), 10)
    chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    code = "".join(random.choice(chars) for _ in range(length))
    
    return {
        "value": code,
        "length": len(code),
    }


def _gen_identity(params):
    gender = params.get("gender", random.choice(["male", "female"]))
    
    surnames = ["王", "李", "张", "刘", "陈", "杨", "黄", "赵", "周", "吴", "徐", "孙", "马", "朱", "胡", "郭", "何", "高", "林", "罗"]
    male_names = ["伟", "强", "磊", "军", "勇", "杰", "涛", "明", "辉", "鹏", "浩", "宇", "轩", "子涵", "浩然"]
    female_names = ["芳", "敏", "静", "丽", "婷", "雪", "玲", "娟", "艳", "娜", "诗涵", "欣怡", "梓涵", "雨桐", "一诺"]
    
    surname = random.choice(surnames)
    if gender == "male":
        given = random.choice(male_names) + random.choice(male_names)
    else:
        given = random.choice(female_names) + random.choice(female_names)
    
    name = surname + given
    
    # 生成身份证号
    area_code = random.choice(["110101", "310101", "440103", "510104", "320102"])
    birth = f"{random.randint(1970, 2005):04d}{random.randint(1,12):02d}{random.randint(1,28):02d}"
    seq = f"{random.randint(0,999):03d}"
    gender_digit = str(random.randint(1, 9)) if gender == "male" else str(random.randint(0, 8))
    
    phone_prefixes = ["138", "139", "150", "158", "186", "189", "176", "199"]
    phone = random.choice(phone_prefixes) + "".join(str(random.randint(0, 9)) for _ in range(8))
    
    email_domains = ["qq.com", "163.com", "gmail.com", "outlook.com", "icloud.com"]
    email = f"{phone}@{random.choice(email_domains)}"
    
    return {
        "name": name,
        "gender": "男" if gender == "male" else "女",
        "phone": phone,
        "email": email,
        "id_number": f"{area_code}{birth}{seq}{gender_digit}",
    }


def _gen_lorem(params):
    paragraphs = min(int(params.get("paragraphs", 3)), 10)
    
    lorem_words = [
        "lorem", "ipsum", "dolor", "sit", "amet", "consectetur", "adipiscing", "elit",
        "sed", "do", "eiusmod", "tempor", "incididunt", "ut", "labore", "et", "dolore",
        "magna", "aliqua", "enim", "ad", "minim", "veniam", "quis", "nostrud",
        "exercitation", "ullamco", "laboris", "nisi", "ut", "aliquip", "ex", "ea",
        "commodo", "consequat", "duis", "aute", "irure", "dolor", "in", "reprehenderit",
        "voluptate", "velit", "esse", "cillum", "dolore", "eu", "fugiat", "nulla", "pariatur",
    ]
    
    # 中文占位文本
    cn_words = [
        "生活", "世界", "时间", "空间", "未来", "现在", "过去", "一切", "所有",
        "美好", "快乐", "幸福", "梦想", "希望", "努力", "成功", "失败", "成长",
        "学习", "工作", "家庭", "朋友", "爱情", "自由", "和平", "发展", "创新",
    ]
    
    text_parts = []
    for _ in range(paragraphs):
        para = []
        for _ in range(random.randint(4, 8)):
            sentence = "".join(random.choice(cn_words) for _ in range(random.randint(5, 15)))
            para.append(sentence)
        text_parts.append("，".join(para) + "。")
    
    return {
        "value": "\n\n".join(text_parts),
        "paragraphs": paragraphs,
        "language": "zh-CN",
    }


def _gen_random_number(params):
    min_val = int(params.get("min", 1))
    max_val = int(params.get("max", 100))
    
    num = random.randint(min_val, max_val)
    return {"value": num, "range": f"{min_val} ~ {max_val}"}


def _gen_hash(params):
    text = params.get("text", str(random.randint(100000, 999999)))
    algo = params.get("algo", "sha256")
    
    hash_funcs = {
        "md5": hashlib.md5,
        "sha1": hashlib.sha1,
        "sha256": hashlib.sha256,
        "sha512": hashlib.sha512,
    }
    
    func = hash_funcs.get(algo, hashlib.sha256)
    hash_val = func(text.encode()).hexdigest()
    
    return {"value": hash_val, "input": text, "algorithm": algo, "length": len(hash_val)}


def _gen_token(params):
    length = min(int(params.get("length", 32)), 256)
    token = "".join(random.choice(string.ascii_letters + string.digits + "-_") for _ in range(length))
    
    return {"value": token, "length": len(token)}


def _gen_username(params):
    prefixes = ["user", "admin", "guest", "member", "player", "coder", "dev", "designer", "writer", "creator"]
    prefix = random.choice(prefixes)
    suffix = "".join(str(random.randint(0, 9)) for _ in range(4))
    
    return {"value": f"{prefix}{suffix}"}


def _gen_email(params):
    domains = ["gmail.com", "outlook.com", "yahoo.com", "proton.me", "qq.com", "163.com"]
    username = _gen_username(params)["value"]
    domain = random.choice(domains)
    
    return {"value": f"{username}@{domain}"}


def _gen_phone(params):
    prefixes = ["138", "139", "150", "158", "186", "189", "176", "199", "135", "188"]
    prefix = random.choice(prefixes)
    suffix = "".join(str(random.randint(0, 9)) for _ in range(8))
    
    return {"value": f"{prefix}{suffix}"}


def _gen_address(params):
    provinces = ["北京市", "上海市", "广东省", "浙江省", "江苏省", "四川省", "湖北省", "湖南省"]
    cities = ["市辖区", "浦东新区", "广州市", "杭州市", "南京市", "成都市", "武汉市", "长沙市"]
    districts = ["朝阳区", "黄浦区", "天河区", "西湖区", "鼓楼区", "武侯区", "洪山区", "岳麓区"]
    
    province = random.choice(provinces)
    city = random.choice(cities)
    district = random.choice(districts)
    street = f"{random.choice(['中山', '人民', '建设', '文化', '解放'])}路{random.randint(1, 500)}号"
    
    return {"value": f"{province}{city}{district}{street}"}


def _gen_company(params):
    prefixes = ["星辰", "华宇", "鼎新", "瑞丰", "中科", "天元", "博雅", "云帆"]
    suffixes = ["科技", "集团", "控股", "实业", "投资", "咨询", "数字", "智能"]
    
    name = random.choice(prefixes) + random.choice(suffixes)
    return {"value": f"{name}有限公司"}


def _gen_credit_card(params):
    # 测试卡号（非真实）
    cards = [
        "4532015112830366",
        "4916481234567890",
        "5425233430109903",
        "374245455400126",
    ]
    return {"value": random.choice(cards), "note": "仅为格式示例，非真实卡号"}


# 需要在文件顶部添加
import re