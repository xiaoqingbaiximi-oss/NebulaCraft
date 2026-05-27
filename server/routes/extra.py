"""
扩展工具 API - 增强版
支持: 天气 / IP / 笑话 / 诗词 / 成语 / 倒计时 / 单位换算 / 字数统计 / 农历 / 汇率 / 简繁 / 进制 / 颜色 / 音乐
"""
import re
import random
import json
import os
from datetime import datetime, timedelta
from server.config import DATA_DIR
from server.services.music_gen import music_gen

# 本地数据缓存
CACHE_DIR = os.path.join(DATA_DIR, "cache")
os.makedirs(CACHE_DIR, exist_ok=True)


def handle(body):
    msg = body.get("message", "").strip()
    action = body.get("action", "")

    if not msg and not action:
        return {"ok": False, "error": "请输入内容"}

    # 指令路由表
    routes = [
        (["天气", "weather"], lambda: weather(msg)),
        (["IP", "ip"], lambda: ip_lookup(msg)),
        (["名言", "名句", "quote"], lambda: quote()),
        (["笑话", "段子", "joke"], lambda: joke()),
        (["倒计时", "countdown"], lambda: countdown(msg)),
        (["诗词", "古诗", "poem"], lambda: poem()),
        (["成语", "idiom"], lambda: idiom(msg)),
        (["手机", "phone"], lambda: phone_lookup(msg)),
        (["农历", "lunar"], lambda: lunar_date()),
        (["汇率", "exchange"], lambda: exchange_rate(msg)),
        (["统计字数", "字数", "wordcount"], lambda: word_count(msg)),
        (["繁体", "简繁"], lambda: to_traditional(msg)),
        (["简体"], lambda: to_simplified(msg)),
        (["进制", "base"], lambda: base_convert(msg)),
        (["颜色", "color"], lambda: color_name(msg)),
        (["单位换算", "换算", "convert"], lambda: unit_convert(msg)),
        (["音乐", "music", "作曲"], lambda: generate_music(msg)),
    ]

    # 分离指令前缀
    for prefixes, func in routes:
        for prefix in prefixes:
            if msg.startswith(prefix) or action == prefix.lower():
                return func()

    return {"ok": False, "error": "无法识别，试试: 天气 北京 / 笑话 / 名言 / 倒计时 2025-01-01"}


def generate_music(msg):
    """生成音乐"""
    prompt = msg.replace("音乐", "").replace("music", "").replace("作曲", "").strip()
    if prompt:
        result = music_gen.text_to_music(prompt)
    else:
        result = music_gen.generate_full(style="happy", tempo=120, measures=16)
    if result.get("ok"):
        result["result"] = f"🎵 已生成 {result.get('style', '音乐')}\n节拍: {result.get('tempo', 120)} BPM\n格式: {result.get('format', 'midi').upper()}\n[试听]({result['url']}) | [下载]({result['url']})"
    return result


def weather(msg):
    city = msg.replace("天气", "").replace("weather", "").strip()
    if not city:
        city = "北京"

    try:
        import requests
        resp = requests.get(
            f"https://wttr.in/{city}?format=j1&lang=zh",
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        data = resp.json()

        current = data.get("current_condition", [{}])[0]
        weather_info = data.get("weather", [{}])[0]

        temp = current.get("temp_C", "N/A")
        humidity = current.get("humidity", "N/A")
        wind = current.get("windSpeedKmph", "N/A")
        desc = current.get("weatherDesc", [{}])[0].get("value", "")

        max_temp = weather_info.get("maxtempC", "N/A")
        min_temp = weather_info.get("mintempC", "N/A")

        return {
            "ok": True,
            "result": (
                f"🌤️ {city}\n"
                f"当前温度: {temp}°C\n"
                f"天气: {desc}\n"
                f"最高/最低: {max_temp}°C / {min_temp}°C\n"
                f"湿度: {humidity}%\n"
                f"风速: {wind} km/h"
            ),
            "data": {
                "city": city,
                "temp": temp,
                "desc": desc,
                "humidity": humidity,
            }
        }
    except:
        return {"ok": True, "result": f"🌤️ {city}: 晴天 22°C\n💡 离线模式，联网可获取实时天气"}


def ip_lookup(msg):
    ip = msg.replace("IP", "").replace("ip", "").strip()
    if not ip:
        import socket
        ip = socket.gethostbyname(socket.gethostname())

    try:
        import requests
        resp = requests.get(f"http://ip-api.com/json/{ip}?lang=zh-CN", timeout=10)
        d = resp.json()
        if d.get("status") == "success":
            return {
                "ok": True,
                "result": (
                    f"📍 IP: {d['query']}\n"
                    f"国家: {d['country']}\n"
                    f"地区: {d['regionName']}\n"
                    f"城市: {d['city']}\n"
                    f"运营商: {d['isp']}\n"
                    f"经纬度: {d['lat']}, {d['lon']}"
                )
            }
    except:
        pass
    return {"ok": True, "result": f"📍 IP: {ip}\n（离线模式，无法查询归属地）"}


def quote():
    quotes = [
        ("人生最大的敌人是自己。", "佛家"),
        ("千里之行，始于足下。", "老子"),
        ("学而不思则罔，思而不学则殆。", "孔子"),
        ("天行健，君子以自强不息。", "《周易》"),
        ("世界上最快乐的事，莫过于为理想而奋斗。", "苏格拉底"),
        ("活着就是为了改变世界。", "乔布斯"),
        ("要么你主宰生活，要么你被生活主宰。", "吉姆·罗恩"),
        ("不要等待机会，而要创造机会。", "培根"),
        ("成功是1%的天赋加上99%的汗水。", "爱迪生"),
        ("想象力比知识更重要。", "爱因斯坦"),
    ]
    quote_text, author = random.choice(quotes)
    return {"ok": True, "result": f"💬 {quote_text}\n—— {author}"}


def joke():
    jokes = [
        "程序员最怕什么？\n最怕老婆说：你帮我修一下电脑吧。",
        "为什么程序员喜欢深色模式？\n因为光会吸引bug。",
        "一个函数走进酒吧，\n酒保说：对不起，我们不接待函数。\n函数说：没关系，我也不期待。",
        "产品经理：这个需求很简单。\n程序员：……（内心：世界末日）",
        "0和8在路上相遇，\n0对8说：胖就胖呗，还系什么腰带！",
        "Chuck Norris 的代码不需要注释。\n代码会自动解释给其他开发者看。",
        "老板：这个bug你能修复吗？\n程序员：当然能，但我不确定计算机能不能运行我的意志力。",
    ]
    return {"ok": True, "result": f"😀 {random.choice(jokes)}"}


def countdown(msg):
    target = msg.replace("倒计时", "").replace("countdown", "").strip()

    try:
        dt = datetime.strptime(target, "%Y-%m-%d")
        now = datetime.now()
        diff = dt - now
        days = diff.days

        if days < 0:
            return {"ok": True, "result": f"📮 {target} 已经过去 {abs(days)} 天"}

        weeks = days // 7
        months = days // 30
        years = days // 365

        return {
            "ok": True,
            "result": (
                f"📮 距离 {target} 还有:\n"
                f"{days} 天\n"
                f"约 {weeks} 周 / {months} 个月 / {years} 年\n"
                f"⏰ {diff.seconds // 3600} 小时 {diff.seconds % 3600 // 60} 分钟"
            ),
        }
    except:
        return {"ok": False, "error": "日期格式: 倒计时 YYYY-MM-DD"}


def poem():
    poems = [
        ("静夜思", "李白", "床前明月光，疑是地上霜。\n举头望明月，低头思故乡。"),
        ("登鹳雀楼", "王之涣", "白日依山尽，黄河入海流。\n欲穷千里目，更上一层楼。"),
        ("春晓", "孟浩然", "春眠不觉晓，处处闻啼鸟。\n夜来风雨声，花落知多少。"),
        ("悯农", "李绅", "锄禾日当午，汗滴禾下土。\n谁知盘中餐，粒粒皆辛苦。"),
        ("江雪", "柳宗元", "千山鸟飞绝，万径人踪灭。\n孤舟蓑笠翁，独钓寒江雪。"),
    ]
    title, author, content = random.choice(poems)
    return {"ok": True, "result": f"📜 《{title}》—— {author}\n\n{content}"}


def idiom(msg):
    word = msg.replace("成语", "").replace("idiom", "").strip()

    idioms_db = {
        "一心一意": {"explanation": "形容心思专一，没有杂念。", "source": "《三国志》"},
        "画蛇添足": {"explanation": "比喻多此一举，反而坏事。", "source": "《战国策》"},
        "守株待兔": {"explanation": "比喻不劳而获，也讽刺死守狭隘经验。", "source": "《韩非子》"},
        "掩耳盗铃": {"explanation": "比喻自欺欺人。", "source": "《吕氏春秋》"},
        "亡羊补牢": {"explanation": "比喻出了问题后想办法补救。", "source": "《战国策》"},
        "井底之蛙": {"explanation": "比喻见识短浅的人。", "source": "《庄子》"},
        "狐假虎威": {"explanation": "比喻仗着别人的势力欺压人。", "source": "《战国策》"},
        "叶公好龙": {"explanation": "比喻口头上爱好，实际上惧怕。", "source": "《新序》"},
    }

    if word in idioms_db:
        info = idioms_db[word]
        return {"ok": True, "result": f"📉 {word}\n释义: {info['explanation']}\n出处: {info['source']}"}

    return {"ok": True, "result": f"📉 {word}\n暂未收录此成语，试试: 一心一意、画蛇添足、守株待兔"}


def phone_lookup(msg):
    phone = msg.replace("手机", "").replace("phone", "").strip()

    if len(phone) < 7:
        return {"ok": False, "error": "请输入正确的手机号"}

    prefix_map = {
        "134": "中国移动", "135": "中国移动", "136": "中国移动", "137": "中国移动",
        "138": "中国移动", "139": "中国移动", "150": "中国移动", "151": "中国移动",
        "152": "中国移动", "157": "中国移动", "158": "中国移动", "159": "中国移动",
        "130": "中国联通", "131": "中国联通", "132": "中国联通", "155": "中国联通",
        "156": "中国联通", "185": "中国联通", "186": "中国联通", "176": "中国联通",
        "133": "中国电信", "153": "中国电信", "180": "中国电信", "189": "中国电信",
        "177": "中国电信", "199": "中国电信",
    }

    prefix = phone[:3]
    operator = prefix_map.get(prefix, "未知运营商")

    return {"ok": True, "result": f"📫 {phone}\n运营商: {operator}\n💡 完整归属地需联网查询"}


def lunar_date():
    now = datetime.now()
    return {
        "ok": True,
        "result": (
            f"📅 公历: {now.strftime('%Y-%m-%d %A')}\n"
            f"🌙 农历: 需要安装 lunar-python 获取精确农历\n"
            f"⏰ 时间: {now.strftime('%H:%M:%S')}\n"
            f"📅 周数: 第{now.isocalendar()[1]}周"
        ),
    }


def exchange_rate(msg):
    parts = msg.replace("汇率", "").replace("exchange", "").strip().split()

    rates = {
        "USD": 7.24, "EUR": 7.85, "JPY": 0.048, "GBP": 9.15,
        "KRW": 0.0054, "HKD": 0.93, "AUD": 4.72, "CAD": 5.30,
        "SGD": 5.38, "THB": 0.20, "CNY": 1.0,
    }

    if len(parts) == 0:
        result = "💶 参考汇率（1 CNY =）:\n" + "\n".join(
            [f"  {code}: {1/rate:.4f}" for code, rate in rates.items() if code != "CNY"]
        )
        return {"ok": True, "result": result}

    if len(parts) >= 2:
        frm = parts[0].upper()
        to = parts[1].upper()

        if frm in rates and to in rates:
            result = rates[to] / rates[frm]
            return {"ok": True, "result": f"💶 1 {frm} = {result:.4f} {to}\n（参考汇率，实际以银行为准）"}

    return {"ok": False, "error": "格式: 汇率 USD CNY"}


def word_count(msg):
    text = msg.replace("统计字数", "").replace("字数", "").replace("wordcount", "").strip()

    if not text:
        return {"ok": True, "result": "请粘贴文本: 统计字数 xxx"}

    chars = len(text)
    chars_no_space = len(text.replace(" ", "").replace("\n", ""))
    words_en = len(text.split())
    words_cn = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    lines = text.count('\n') + 1
    paragraphs = len([p for p in text.split('\n\n') if p.strip()])

    return {
        "ok": True,
        "result": (
            f"📑 字数统计:\n"
            f"总字符: {chars}\n"
            f"不含空格: {chars_no_space}\n"
            f"英文词数: {words_en}\n"
            f"中文字数: {words_cn}\n"
            f"行数: {lines}\n"
            f"段落数: {paragraphs}"
        ),
    }


def to_traditional(msg):
    text = msg.replace("繁体", "").replace("简繁", "").strip()

    mapping = {
        "国": "國", "学": "學", "书": "書", "电": "電", "脑": "腦",
        "见": "見", "说": "說", "话": "話", "爱": "愛", "你": "妳",
        "我": "我", "是": "是", "的": "的", "在": "在", "有": "有",
        "不": "不", "人": "人", "这": "這", "那": "那", "和": "和",
    }

    result = "".join(mapping.get(c, c) for c in text)
    return {"ok": True, "result": f"繁体: {result}"}


def to_simplified(msg):
    text = msg.replace("简体", "").strip()

    mapping = {
        "國": "国", "學": "学", "書": "书", "電": "电", "腦": "脑",
        "見": "见", "說": "说", "話": "话", "愛": "爱", "妳": "你",
    }

    result = "".join(mapping.get(c, c) for c in text)
    return {"ok": True, "result": f"简体: {result}"}


def base_convert(msg):
    parts = msg.replace("进制", "").replace("base", "").strip().split()

    if len(parts) >= 2:
        try:
            num = parts[0]
            spec = parts[1] if len(parts) > 1 else "10to16"

            if "to" in spec:
                frm, to = spec.split("to")
                frm = int(frm)
                to = int(to)

                decimal = int(num, frm)

                if to == 16:
                    result = hex(decimal)[2:]
                elif to == 2:
                    result = bin(decimal)[2:]
                elif to == 8:
                    result = oct(decimal)[2:]
                elif to == 10:
                    result = str(decimal)
                else:
                    result = format(decimal, 'd')

                return {"ok": True, "result": f"🔢 {num}({frm}进制) = {result}({to}进制)"}
        except:
            pass

    return {"ok": False, "error": "格式: 进制 255 10to16"}


def color_name(msg):
    color = msg.replace("颜色", "").replace("color", "").strip()

    colors_map = {
        "#ff0000": "红色 Red",
        "#ff6600": "橙色 Orange",
        "#ffff00": "黄色 Yellow",
        "#00ff00": "绿色 Green",
        "#0000ff": "蓝色 Blue",
        "#6600ff": "紫色 Purple",
        "#ff00ff": "品红 Magenta",
        "#00ffff": "青色 Cyan",
        "#000000": "黑色 Black",
        "#ffffff": "白色 White",
        "#808080": "灰色 Gray",
        "#6c5ce7": "星云紫 Nebula Purple",
    }

    color = color.lower()
    if color in colors_map:
        return {"ok": True, "result": f"🎨 {color} → {colors_map[color]}"}

    return {"ok": True, "result": f"🎨 {color}\n暂无对应名称，试试 #ff0000、#00ff00 等"}


def unit_convert(msg):
    text = msg.replace("单位换算", "").replace("换算", "").replace("convert", "").strip()

    conversions = {
        ("km", "mile"): 0.621371, ("mile", "km"): 1.60934,
        ("kg", "lb"): 2.20462, ("lb", "kg"): 0.453592,
        ("m", "ft"): 3.28084, ("ft", "m"): 0.3048,
        ("cm", "inch"): 0.393701, ("inch", "cm"): 2.54,
        ("l", "gal"): 0.264172, ("gal", "l"): 3.78541,
        ("g", "oz"): 0.035274, ("oz", "g"): 28.3495,
    }

    m = re.search(r'([\d.]+)\s*([a-zA-Z]+)\s*(?:转|转换为|to|->|→)\s*([a-zA-Z]+)', text)
    if m:
        val = float(m.group(1))
        frm = m.group(2).lower()
        to = m.group(3).lower()

        if frm == to:
            return {"ok": True, "result": f"{val} {frm} = {val} {to}"}

        if (frm, to) in conversions:
            result = val * conversions[(frm, to)]
            return {"ok": True, "result": f"📹 {val} {frm} = {result:.4f} {to}"}

        if frm == "c" and to == "f":
            result = val * 9 / 5 + 32
            return {"ok": True, "result": f"🌡️ {val}°C = {result:.1f}°F"}
        if frm == "f" and to == "c":
            result = (val - 32) * 5 / 9
            return {"ok": True, "result": f"🌡️ {val}°F = {result:.1f}°C"}

        return {"ok": False, "error": f"不支持 {frm} → {to}，支持: km/mile, kg/lb, m/ft, cm/inch, l/gal, C/F"}

    result = "📹 支持的单位换算:\n"
    for (frm, to), rate in conversions.items():
        result += f"  {frm} → {to} (×{rate:.4f})\n"
    result += "  温度: C → F\n"
    result += "格式: 1km转mile / 100C转换为F"

    return {"ok": True, "result": result}