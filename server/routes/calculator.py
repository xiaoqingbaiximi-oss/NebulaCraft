"""
计算器 API - 增强版
支持: BMI / 房贷 / 折扣 / 数学 / 日期 / 百分比 / 储蓄 / 税费
"""
import re
import math
from datetime import datetime, timedelta


def handle(body):
    expr = body.get("expression", "").strip()
    if not expr:
        return {"ok": False, "error": "请输入计算表达式"}
    
    # 房贷计算
    loan = re.search(r'房贷\s+(\d+\.?\d*)\s+(\d+\.?\d*)\s+(\d+)', expr)
    if loan:
        return _calculate_loan(
            float(loan.group(1)),
            float(loan.group(2)),
            int(loan.group(3))
        )
    
    # BMI
    bmi = re.search(r'BMI\s+(\d+\.?\d*)\s+(\d+\.?\d*)', expr, re.I)
    if bmi:
        return _calculate_bmi(float(bmi.group(1)), float(bmi.group(2)))
    
    # 折扣
    disc = re.search(r'折扣\s+(\d+\.?\d*)\s+(\d+\.?\d*)', expr)
    if disc:
        return _calculate_discount(float(disc.group(1)), float(disc.group(2)))
    
    # 日期差
    date_diff = re.search(r'日期差\s+(\d{4}-\d{2}-\d{2})\s+(\d{4}-\d{2}-\d{2})', expr)
    if date_diff:
        return _date_diff(date_diff.group(1), date_diff.group(2))
    
    # 日期加减
    date_add = re.search(r'日期\s+(\d{4}-\d{2}-\d{2})\s*\+\s*(\d+)\s*(天|月|年)', expr)
    if date_add:
        return _date_add(date_add.group(1), int(date_add.group(2)), date_add.group(3))
    
    # 百分比
    pct = re.search(r'百分比\s+(\d+\.?\d*)\s+(\d+\.?\d*)', expr)
    if pct:
        return _percentage(float(pct.group(1)), float(pct.group(2)))
    
    # 储蓄计算
    savings = re.search(r'储蓄\s+(\d+\.?\d*)\s+(\d+\.?\d*)\s+(\d+)', expr)
    if savings:
        return _calculate_savings(
            float(savings.group(1)),
            float(savings.group(2)),
            int(savings.group(3))
        )
    
    # 税费
    tax = re.search(r'税费\s+(\d+\.?\d*)', expr)
    if tax:
        return _calculate_tax(float(tax.group(1)))
    
    # 数学表达式
    try:
        if re.match(r'^[\d\s+\-*/().%^!sqrtlogabsincossintanpiEe]+$', expr):
            safe_dict = {
                "math": math,
                "sqrt": math.sqrt, "log": math.log, "log10": math.log10,
                "sin": math.sin, "cos": math.cos, "tan": math.tan,
                "abs": abs, "round": round, "pi": math.pi, "e": math.e,
                "factorial": math.factorial, "pow": math.pow,
            }
            result = eval(expr, {"__builtins__": {}}, safe_dict)
            return {"ok": True, "result": f"{expr} = {result}", "value": result}
    except:
        pass
    
    return {"ok": False, "error": "无法识别，试试: BMI 70 170 / 房贷 1000000 4.9 30 / 日期差 2024-01-01 2024-12-31"}


def _calculate_bmi(weight_kg, height_cm):
    height_m = height_cm / 100
    bmi = weight_kg / (height_m * height_m)
    
    if bmi < 18.5:
        level = "偏瘦 ⚠️"
        advice = "建议增加营养摄入，适当增重"
    elif bmi < 24:
        level = "正常 ✅"
        advice = "体重在健康范围内，保持良好生活习惯"
    elif bmi < 28:
        level = "偏胖 ⚠️"
        advice = "建议控制饮食，增加运动量"
    elif bmi < 32:
        level = "肥胖 ❌"
        advice = "建议制定减重计划，咨询医生"
    else:
        level = "重度肥胖 ❌"
        advice = "建议尽快就医，制定健康管理方案"
    
    ideal_min = round(18.5 * height_m * height_m, 1)
    ideal_max = round(24 * height_m * height_m, 1)
    
    return {
        "ok": True,
        "result": f"BMI: {bmi:.1f} ({level})\n理想体重范围: {ideal_min} ~ {ideal_max} kg\n💡 {advice}",
        "bmi": round(bmi, 1),
        "level": level,
        "ideal_weight": f"{ideal_min} ~ {ideal_max} kg",
    }


def _calculate_loan(amount, rate, years):
    months = years * 12
    monthly_rate = rate / 1200
    
    if monthly_rate > 0:
        monthly_payment = amount * monthly_rate * (1 + monthly_rate) ** months / ((1 + monthly_rate) ** months - 1)
    else:
        monthly_payment = amount / months
    
    total = monthly_payment * months
    interest = total - amount
    
    return {
        "ok": True,
        "result": (
            f"贷款金额: ¥{amount:,.0f}\n"
            f"年利率: {rate}%\n"
            f"期限: {years}年 ({months}个月)\n"
            f"月供: ¥{monthly_payment:,.0f}\n"
            f"总还款: ¥{total:,.0f}\n"
            f"利息总额: ¥{interest:,.0f}\n"
            f"利息占比: {interest/total*100:.1f}%"
        ),
        "monthly": round(monthly_payment, 2),
        "total": round(total, 2),
        "interest": round(interest, 2),
    }


def _calculate_discount(price, off_percent):
    final = price * (1 - off_percent / 100)
    saved = price - final
    
    return {
        "ok": True,
        "result": f"原价: ¥{price:.2f}\n折扣: {off_percent}%\n折后: ¥{final:.2f}\n节省: ¥{saved:.2f}",
        "final_price": round(final, 2),
        "saved": round(saved, 2),
    }


def _date_diff(date1, date2):
    try:
        d1 = datetime.strptime(date1, "%Y-%m-%d")
        d2 = datetime.strptime(date2, "%Y-%m-%d")
        diff = abs((d2 - d1).days)
        
        weeks = diff // 7
        months = diff // 30
        years = diff // 365
        
        return {
            "ok": True,
            "result": (
                f"日期: {date1} → {date2}\n"
                f"相差: {diff} 天\n"
                f"约 {weeks} 周 / {months} 个月 / {years} 年"
            ),
            "days": diff,
        }
    except:
        return {"ok": False, "error": "日期格式错误，使用 YYYY-MM-DD"}


def _date_add(date_str, num, unit):
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        if unit == "天":
            new_dt = dt + timedelta(days=num)
        elif unit == "月":
            month = dt.month + num
            year = dt.year + (month - 1) // 12
            month = (month - 1) % 12 + 1
            day = min(dt.day, [31, 29 if year % 4 == 0 else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
            new_dt = dt.replace(year=year, month=month, day=day)
        elif unit == "年":
            new_dt = dt.replace(year=dt.year + num)
        else:
            return {"ok": False, "error": "单位: 天/月/年"}
        
        return {"ok": True, "result": f"{date_str} + {num}{unit} = {new_dt.strftime('%Y-%m-%d')}"}
    except:
        return {"ok": False, "error": "日期格式错误"}


def _percentage(num, total):
    pct = (num / total) * 100 if total != 0 else 0
    
    return {
        "ok": True,
        "result": f"{num} 占 {total} 的 {pct:.1f}%\n\n{total} 的 {pct:.1f}% = {num}\n{total} 的 1% = {total/100:.2f}",
    }


def _calculate_savings(principal, rate, years):
    total = principal
    detail = []
    
    for y in range(1, years + 1):
        interest = total * rate / 100
        total += interest
        detail.append(f"第{y}年: ¥{total:,.0f} (+¥{interest:,.0f})")
    
    return {
        "ok": True,
        "result": (
            f"本金: ¥{principal:,.0f}\n"
            f"年利率: {rate}%\n"
            f"期限: {years}年\n"
            f"最终金额: ¥{total:,.0f}\n"
            f"利息总额: ¥{total - principal:,.0f}\n\n"
            + "\n".join(detail[:10])
        ),
    }


def _calculate_tax(income):
    """简易个税计算（中国）"""
    taxable = income - 5000  # 起征点
    
    if taxable <= 0:
        tax = 0
        rate = "0%"
    elif taxable <= 3000:
        tax = taxable * 0.03
        rate = "3%"
    elif taxable <= 12000:
        tax = taxable * 0.1 - 210
        rate = "10%"
    elif taxable <= 25000:
        tax = taxable * 0.2 - 1410
        rate = "20%"
    elif taxable <= 35000:
        tax = taxable * 0.25 - 2660
        rate = "25%"
    elif taxable <= 55000:
        tax = taxable * 0.3 - 4410
        rate = "30%"
    elif taxable <= 80000:
        tax = taxable * 0.35 - 7160
        rate = "35%"
    else:
        tax = taxable * 0.45 - 15160
        rate = "45%"
    
    tax = max(0, tax)
    after_tax = income - tax
    
    return {
        "ok": True,
        "result": (
            f"月收入: ¥{income:,.0f}\n"
            f"应纳税所得额: ¥{max(0, taxable):,.0f}\n"
            f"适用税率: {rate}\n"
            f"个税: ¥{tax:,.0f}\n"
            f"税后收入: ¥{after_tax:,.0f}\n\n"
            f"💡 此为简易估算，未含专项扣除"
        ),
    }