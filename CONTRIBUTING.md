# 贡献指南

感谢你对 NebulaCraft 的关注！这份指南将帮助你了解如何参与项目。

## 行为准则

- 尊重所有贡献者
- 建设性讨论，不人身攻击
- 帮助新手，分享知识

## 如何贡献

### 报告 Bug

1. 在 [Issues](https://github.com/xiaoqingbaiximi-oss/NebulaCraft/issues) 中创建新 Issue
2. 标题简洁描述问题
3. 内容包含：
   - **做了什么操作**
   - **期望发生什么**
   - **实际发生了什么**
   - **你的系统环境**（Windows 版本、Python 版本）
   - **截图或日志**（如有）

### 建议新功能

1. 先搜索现有 Issues，避免重复
2. 在 [Discussions](https://github.com/xiaoqingbaiximi-oss/NebulaCraft/discussions) 的"想法与建议"类别中发帖
3. 描述功能场景和使用价值

### 开发插件

NebulaCraft 支持动态加载插件。开发一个插件非常简单：

1. 复制 `data/plugins/hello_world/` 目录
2. 修改 `manifest.json`：
   ```json
   {
     "name": "my_plugin",
     "version": "1.0.0",
     "description": "我的插件",
     "entry": "main"
   }

3. 在 `main.py` 中实现功能：
   ```python
   class Plugin:
       def on_load(self):
           print("插件已加载")
       
       def execute(self, params):
           return {"ok": True, "result": "Hello!"}

重启 NebulaCraft 即可加载

提交代码
Fork 本仓库
创建功能分支：git checkout -b feat/your-feature
编写代码，保持风格一致
提交前测试功能是否正常
提交 PR 到 main 分支
PR 标题清晰描述改动内容
代码风格
Python：遵循 PEP 8
JavaScript：使用 ES6+ 语法，缩进 4 空格
CSS：类名使用小写 + 连字符
函数和类添加简要注释
保持代码简洁，避免过度抽象

Python：遵循 PEP 8
JavaScript：使用 ES6+ 语法，缩进 4 空格
CSS：类名使用小写 + 连字符
函数和类添加简要注释
保持代码简洁，避免过度抽象

项目结构
NebulaCraft/
├── server/           # Python 后端
│   ├── main.py      # 启动入口
│   ├── handler.py   # HTTP 请求处理
│   ├── routes/      # API 路由（每个功能一个文件）
│   └── services/    # 服务层（业务逻辑）
├── js/               # 前端 JavaScript
├── css/              # 样式文件
├── data/             # 运行时数据
│   └── plugins/      # 插件目录
├── index.html        # 主页面
└── requirements.txt  # Python 依赖

问题反馈优先级
类型	处理优先级
安全漏洞	🔴 最高，24小时内响应
核心功能 Bug	🟡 高，3天内响应
插件问题	🟡 中，一周内响应
功能建议	🟢 讨论后决定

许可证
贡献的代码将采用与项目相同的 MIT License。

再次感谢你的贡献！🎉

---

## 第二步：开启 GitHub Discussions

1. 打开仓库页面：`https://github.com/xiaoqingbaiximi-oss/NebulaCraft`
2. 点击顶部 **Settings** 选项卡
3. 左侧菜单往下滚动，找到 **Features** 部分
4. 勾选 **Discussions** ✅
5. 页面会自动刷新，仓库顶部会出现 **Discussions** 标签

### 创建讨论类别

点击 Discussions 标签 → **New category**，创建以下类别：

| 类别名 | 格式 | 说明 |
|--------|------|------|
| 💡 想法与建议 | Ideas | 新功能提议、改进建议 |
| 🔌 插件分享 | Show and tell | 分享自己开发的插件 |
| ❓ 问答求助 | Q&A | 使用问题、技术求助 |
| 📣 展示作品 | Show and tell | 用 NebulaCraft 创作的作品 |

---

## 第三步：更新 README，添加社区链接

在 README 底部的"致谢"章节上方，添加：

```markdown
## 社区

- 💬 [Discussions](https://github.com/xiaoqingbaiximi-oss/NebulaCraft/discussions) — 提问、建议、分享
- 🐛 [Issues](https://github.com/xiaoqingbaiximi-oss/NebulaCraft/issues) — 报告 Bug
- 📖 [贡献指南](CONTRIBUTING.md) — 参与开发