"""API 文档页面"""
import json


def handle_index():
    """返回 API 文档 HTML"""
    routes = [
        {"method": "POST", "path": "/api/chat", "desc": "AI 对话"},
        {"method": "POST", "path": "/api/chat_stream", "desc": "AI 流式对话"},
        {"method": "POST", "path": "/api/chat_search", "desc": "联网搜索对话"},
        {"method": "POST", "path": "/api/calculator", "desc": "万能计算器"},
        {"method": "POST", "path": "/api/generator", "desc": "万能生成器"},
        {"method": "POST", "path": "/api/security", "desc": "安全工具"},
        {"method": "POST", "path": "/api/translate", "desc": "翻译"},
        {"method": "POST", "path": "/api/smart", "desc": "智能指令"},
        {"method": "POST", "path": "/api/extra", "desc": "扩展查询"},
        {"method": "POST", "path": "/api/speech", "desc": "文字转语音"},
        {"method": "POST", "path": "/api/poster", "desc": "海报生成"},
        {"method": "POST", "path": "/api/sd_image", "desc": "AI 图像生成"},
        {"method": "POST", "path": "/api/sd_status", "desc": "SD 后端状态"},
        {"method": "POST", "path": "/api/sd_styles", "desc": "SD 风格列表"},
        {"method": "POST", "path": "/api/knowledge", "desc": "知识库管理"},
        {"method": "POST", "path": "/api/agent", "desc": "Agent 任务执行"},
        {"method": "POST", "path": "/api/agent/tools", "desc": "Agent 工具列表"},
        {"method": "POST", "path": "/api/plugin", "desc": "插件管理"},
        {"method": "POST", "path": "/api/notes", "desc": "笔记管理"},
        {"method": "POST", "path": "/api/share", "desc": "分享创建"},
        {"method": "POST", "path": "/api/export", "desc": "导出 PDF/Word/MD"},
        {"method": "POST", "path": "/api/scraper", "desc": "网页剪藏"},
        {"method": "POST", "path": "/api/rss", "desc": "RSS 订阅"},
        {"method": "GET", "path": "/health", "desc": "健康检查"},
        {"method": "GET", "path": "/api/models/list", "desc": "模型列表"},
    ]

    rows = ""
    for r in routes:
        method_color = "#10b981" if r["method"] == "GET" else "#6c5ce7"
        rows += f"""
        <tr>
            <td><span style="background:{method_color};color:#fff;padding:2px 8px;border-radius:4px;font-size:.8rem;font-weight:700">{r['method']}</span></td>
            <td style="font-family:monospace">{r['path']}</td>
            <td style="color:#9090b8">{r['desc']}</td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NebulaCraft API 文档</title>
    <style>
        *{{margin:0;padding:0;box-sizing:border-box}}
        body{{font-family:'Segoe UI','Microsoft YaHei',sans-serif;background:#0a0a14;color:#e8e8f8;padding:40px 20px}}
        .container{{max-width:900px;margin:0 auto}}
        h1{{font-size:2rem;background:linear-gradient(135deg,#a78bfa,#6c5ce7);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:8px}}
        .subtitle{{color:#9090b8;margin-bottom:32px}}
        table{{width:100%;border-collapse:collapse}}
        th{{text-align:left;padding:12px;border-bottom:2px solid #2a2a48;color:#a78bfa;font-size:.85rem;text-transform:uppercase;letter-spacing:1px}}
        td{{padding:10px 12px;border-bottom:1px solid #1a1a35}}
        tr:hover{{background:rgba(108,92,231,0.05)}}
        .footer{{text-align:center;color:#6b6b80;margin-top:40px;font-size:.8rem}}
        a{{color:#a78bfa;text-decoration:none}}
    </style>
</head>
<body>
    <div class="container">
        <h1>🌌 NebulaCraft API</h1>
        <p class="subtitle">v7.0.0 · 本地全能 AI 工作站 · {len(routes)} 个端点</p>
        <table>
            <thead><tr><th>方法</th><th>路径</th><th>说明</th></tr></thead>
            <tbody>{rows}</tbody>
        </table>
        <div class="footer">
            <p>所有 POST 请求需 <code>Content-Type: application/json</code></p>
            <p style="margin-top:8px"><a href="/">← 返回 NebulaCraft</a></p>
        </div>
    </div>
</body>
</html>"""
    return html