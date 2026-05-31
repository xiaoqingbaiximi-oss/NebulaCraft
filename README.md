好的，以下是 NebulaCraft 的详细介绍，可直接用于 GitHub README。

---

# 🌌 NebulaCraft v28.0

> **本地全能 AI 工作站** — 一个输入框，80+ 工具，零门槛使用

完全本地运行，无需联网，无需注册，数据 100% 隐私安全。

---

## 为什么选择 NebulaCraft？

| 对比 | NebulaCraft | ChatGPT | Midjourney | Cursor |
|------|-------------|---------|------------|--------|
| 运行方式 | **本地** | 云端 | 云端 | 云端 |
| 隐私安全 | ✅ 100% | ❌ | ❌ | ❌ |
| 离线可用 | ✅ | ❌ | ❌ | ❌ |
| 免费 | ✅ 完全免费 | 部分免费 | 付费 | 付费 |
| AI 对话 | ✅ | ✅ | ❌ | ❌ |
| AI 生图 | ✅ 内置引擎 | ❌ | ✅ | ❌ |
| AI 视频 | ✅ | ❌ | ❌ | ❌ |
| 编程助手 | ✅ | 基础 | ❌ | ✅ |
| 工具箱 | **80+** | 插件 | ❌ | ❌ |

---

## 🎥 快速演示

| 思维导图 | AI 生图 | Agent 工作流 |
|:---:|:---:|:---:|
| ![思维导图](demos/demo1.gif) | ![AI生图](demos/demo2.gif) | ![Agent](demos/demo3.gif) |
| *一句话生成可视化* | *聊天框直接出图* | *代码自动生成保存* |

## 核心功能

### 💬 AI 对话
- 多模型支持（Qwen / DeepSeek / Llama / LLaVA）
- 流式输出 + Markdown 渲染
- 联网搜索（自动判断是否需要）
- 对话历史持久化
- 16 个智能指令（润色/简历/食谱/攻略/解题...）
- 语音输入
- 对话模板
- @知识库 自动检索增强

### 🎨 AI 生图
- **完全内置引擎**，无需外部 API
- 海报设计 / 插画 / Logo / 图标 / 写实照片 / 艺术风格
- 支持 SD WebUI 自动检测（可选增强）
- 8 种预设风格

### 🎬 AI 视频
- 文字动画生成
- 幻灯片制作
- 字幕文件生成
- 需要 ffmpeg（可选）

### 💻 编程助手
- 代码补全
- Bug 检测
- 代码审查（可读性/性能/安全/维护性）
- 重构建议
- 测试用例生成
- 代码解释
- 架构评审
- 支持 Python / JavaScript / Java / Go / Rust

### 📚 知识库 RAG
- 文档上传自动向量化
- 语义搜索 + 相似度评分
- 多集合管理
- 对话中 @知识库 自动检索

### 🤖 Agent 工作流
- 多步骤任务自动编排
- 工具链自动调用
- 执行结果 AI 总结

### 🔌 插件系统
- 动态加载/卸载
- 热注册工具
- 示例插件开箱即用

### 🔧 工具箱（25+ 内置工具）
| 分类 | 工具 |
|------|------|
| 📊 计算 | 万能计算器、进制转换、单位换算、时间戳 |
| 🔐 安全 | 密码生成、加密解密、Base64、UUID |
| 📝 写作 | 翻译、字数统计 |
| 🌐 查询 | 天气、IP、笑话、名言、诗词、倒计时、颜色 |
| 🔧 开发 | JSON 格式化、二维码、正则、文本对比、代码沙箱 |
| 📁 文件 | 文件智能分析（20+ 格式） |
| ⏰ 生活 | 番茄钟、习惯打卡、笔记、密码本 |

### 🎨 体验
- 深色/浅色/高对比度主题
- 自定义主题色
- 阅读障碍字体 + 字号调节
- 中英双语
- PWA 安装到桌面
- 移动端适配 + 手势操作
- 键盘快捷键（按 `?` 查看）

### 🔒 安全
- 100% 本地运行，数据不上传
- 代码执行沙箱隔离
- AES 加密密码本
- 请求限流防护
- 端到端加密聊天

### 🏠 电脑管家
- **全面扫描**：CPU/内存/磁盘/启动项/临时文件/网络/安全/更新 8 项检查
- **健康评分**：100 分制，自动评估电脑状态
- **安全修复**：确认后自动修复，所有危险操作需用户确认
- **实时保护**：后台持续监控，CPU/内存异常自动提醒

### 🧠 自主运行核心
- **环境感知**：每 10 秒检测系统状态
- **自主决策**：CPU 过高自动查进程，磁盘满自动清理
- **目标驱动**：用户说目标，AI 自己规划所有步骤
- **自动纠错**：失败后分析原因，生成备选方案重试

### 🔧 自升级引擎
- AI 修改自身代码：说"把端口改成 9999"即可
- 修改前自动备份，可随时回滚
- 支持修改配置、优化功能、新增模块

### 🧠 记忆系统
- 记住用户偏好和习惯
- 根据上下文主动建议

### 📊 系统监控
- CPU/内存/磁盘实时监控
- 进程查看和管理

---

## 快速开始

### Windows
```bash
# 1. 安装 Python 3.10+ → https://www.python.org
# 2. 安装 Ollama → https://ollama.com
# 3. 下载 AI 模型
ollama pull qwen2.5:1.5b
# 4. 双击「一键安装.bat」安装依赖
# 5. 双击「启动.bat」启动
# 6. 浏览器打开 http://localhost:8889
```

### macOS / Linux
```bash
pip install -r requirements.txt
ollama pull qwen2.5:1.5b
python server/main.py
# 浏览器打开 http://localhost:8889
```

### Docker
```bash
docker-compose up -d
# 浏览器打开 http://localhost:8889
```

---

## 快捷键

| 按键 | 功能 |
|------|------|
| `?` | 显示所有快捷键 |
| `Ctrl+K` | 搜索工具 |
| `Ctrl+N` | 新建对话 |
| `Ctrl+B` | 切换侧边栏 |
| `Alt+1/2/3` | 切换视图 |
| `Enter` | 发送消息 |
| `Shift+Enter` | 换行 |
| `Esc` | 关闭面板 |

---

## 对话指令

在输入框直接输入：
```
润色：今天天气真好
简历：前端工程师 3年经验
食谱：红烧肉
攻略：西安3天
BMI 70 170
天气 北京
生成密码
@知识库 什么是机器学习
@搜索 最新AI新闻
@图片 一只可爱的猫
```

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | HTML5 + CSS3 + 原生 JavaScript |
| UI 库 | marked（Markdown）、DOMPurify（XSS）、Chart.js（图表） |
| 后端 | Python 3.10+，内置 http.server |
| AI 引擎 | Ollama（默认 Qwen 2.5 1.5B，支持切换） |
| 图像处理 | Pillow（内置生图引擎） |
| 语音 | Web Speech API（前端）+ edge-tts（后端） |
| 数据库 | SQLite |
| 部署 | Docker、PyInstaller（EXE）、PWA |

---

## 项目结构

```
NebulaCraft/
├── server/               # Python 后端
│   ├── main.py          # 启动入口
│   ├── handler.py       # HTTP 请求处理（90+ 路由）
│   ├── routes/          # API 路由（30+ 模块）
│   └── services/        # 服务层（20+ 模块）
├── js/                   # 前端 JavaScript（20+ 模块）
├── css/                  # 样式（深色/浅色/高对比度）
├── locales/              # 国际化（中英双语）
├── data/                 # 运行时数据
│   ├── plugins/          # 插件目录
│   └── nebulacraft.db    # SQLite 数据库
├── static/               # 静态资源
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── 一键安装.bat
├── 启动.bat
└── README.md
```

---

## 插件开发

```python
# data/plugins/my_plugin/main.py
class Plugin:
    def on_load(self):
        print("Plugin loaded")
    
    def execute(self, params):
        return {"ok": True, "result": "Hello from plugin!"}
```

```json
// data/plugins/my_plugin/manifest.json
{
  "name": "my_plugin",
  "version": "1.0.0",
  "description": "My first plugin",
  "entry": "main"
}
```

---

## API 文档

启动后访问 `http://localhost:8889/docs` 查看完整 API 文档（80+ 端点）。

---

## 常见问题

**Q: 需要联网吗？**
A: 不需要。AI 对话、生图、视频、编程全部本地运行。仅联网搜索功能需要网络。

**Q: 支持哪些 AI 模型？**
A: 所有 Ollama 支持的模型。推荐 Qwen 2.5（中文最佳）、DeepSeek-Coder（编程）、LLaVA（视觉）。

**Q: 如何切换模型？**
A: 侧边栏下拉菜单选择，或 `ollama pull 模型名` 下载新模型。

**Q: 数据存在哪里？**
A: 100% 本地。对话记录在 SQLite 数据库，设置在前端 localStorage。

---

## 许可证

MIT License © 2025 NebulaCraft

---

## 致谢

- [Ollama](https://ollama.com) - 本地 AI 推理引擎
- [marked](https://marked.js.org) - Markdown 渲染
- [DOMPurify](https://github.com/cure53/DOMPurify) - XSS 防护
- [Chart.js](https://www.chartjs.org) - 图表库

---

**🌌 NebulaCraft — 你的本地全能 AI 工作站**