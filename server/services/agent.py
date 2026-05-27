"""
Agent 工作流引擎 - 强化版
支持: 任务规划 / 工具调用 / 代码执行 / 文件操作 / 错误重试 / 自由路径
"""
import json
import re
import os
import subprocess
import tempfile
from server.services.ollama import chat as ollama_chat


class Tool:
    def __init__(self, name, description, func, params_schema=None):
        self.name = name
        self.description = description
        self.func = func
        self.params_schema = params_schema or {}

    def execute(self, params):
        try:
            return self.func(params)
        except Exception as e:
            return {"ok": False, "error": str(e)}


class Agent:
    def __init__(self):
        self.tools = {}
        self.max_steps = 10
        self._register_builtin_tools()

    def _register_builtin_tools(self):
        from server.routes import smart, calculator, generator, extra, translate

        self.register_tool(Tool("smart", "智能指令", smart.handle, {"message": "指令"}))
        self.register_tool(Tool("calculator", "计算器", calculator.handle, {"expression": "表达式"}))
        self.register_tool(Tool("generator", "生成器", generator.handle, {"type": "类型"}))
        self.register_tool(Tool("extra", "查询工具", extra.handle, {"message": "查询内容"}))
        self.register_tool(Tool("translate", "翻译", translate.handle, {"text": "文本", "target": "目标语言"}))
        self.register_tool(Tool("write_file", "保存文件", self._write_file, {"path": "完整路径", "content": "文件内容"}))
        self.register_tool(Tool("read_file", "读取文件", self._read_file, {"path": "文件路径"}))
        self.register_tool(Tool("run_code", "执行代码", self._run_code, {"code": "代码", "language": "python"}))
        self.register_tool(Tool("list_dir", "列出目录", self._list_dir, {"path": "目录路径"}))

    def register_tool(self, tool):
        self.tools[tool.name] = tool

    def get_tools_description(self):
        lines = ["可用工具："]
        for name, tool in self.tools.items():
            lines.append(f"- {name}: {tool.description}")
        return "\n".join(lines)

    def _write_file(self, params):
        path = params.get("path", "")
        content = params.get("content", "")
        if not path:
            return {"ok": False, "error": "请提供文件路径"}
        try:
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return {"ok": True, "path": path, "size": len(content)}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def _read_file(self, params):
        path = params.get("path", "")
        if not path or not os.path.exists(path):
            return {"ok": False, "error": f"文件不存在: {path}"}
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            return {"ok": True, "path": path, "content": content[:5000]}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def _run_code(self, params):
        code = params.get("code", "")
        language = params.get("language", "python").lower()
        if not code:
            return {"ok": False, "error": "请提供代码"}
        try:
            if language == "python":
                result = subprocess.run(["python", "-c", code], capture_output=True, text=True, timeout=30, cwd=tempfile.gettempdir())
            elif language in ("html", "javascript"):
                html_path = os.path.join(tempfile.gettempdir(), "agent_output.html")
                with open(html_path, "w", encoding="utf-8") as f:
                    f.write(code if language == "html" else f"<script>{code}</script>")
                return {"ok": True, "output": f"HTML saved to {html_path}", "path": html_path}
            else:
                return {"ok": False, "error": f"Unsupported language: {language}"}
            return {"ok": True, "output": result.stdout.strip() or "(no output)", "error": result.stderr.strip() or None}
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": "代码执行超时"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def _list_dir(self, params):
        path = params.get("path", ".")
        try:
            items = os.listdir(path)
            dirs = [f"[DIR] {d}" for d in items if os.path.isdir(os.path.join(path, d))]
            files = [f"[FILE] {f}" for f in items if os.path.isfile(os.path.join(path, f))]
            return {"ok": True, "path": path, "items": dirs + files, "count": len(items)}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def plan(self, user_input, context=""):
        if context and context.strip().startswith('{'):
            try:
                predef = json.loads(context)
                if "steps" in predef:
                    return predef["steps"]
            except:
                pass

        system_prompt = """你是任务执行器。必须严格返回JSON步骤。

工具：write_file(保存文件), run_code(执行代码), list_dir(列目录), read_file(读文件)

规则：
1. 需要生成代码的任务：直接生成完整代码，用 write_file 保存
2. 路径由用户在需求中指定，你必须提取并填入 path 参数
3. 如果用户没指定路径，默认用 C:\\Users\\Administrator\\Desktop\\
4. 代码必须完整可运行
5. 最多5步

示例 - 用户说"写个斐波那契保存到 D:\\test\\fib.py"：
{"steps":[{"step":1,"tool":"write_file","params":{"path":"D:\\test\\fib.py","content":"def fib(n):\\n    if n<=1: return n\\n    return fib(n-1)+fib(n-2)\\nprint(fib(20))"},"reason":"生成斐波那契脚本保存到指定路径"}]}

示例 - 用户说"帮我生成一个贪吃蛇游戏放到桌面"：
{"steps":[{"step":1,"tool":"write_file","params":{"path":"C:\\Users\\Administrator\\Desktop\\snake.html","content":"<!DOCTYPE html>..."},"reason":"生成贪吃蛇游戏保存到桌面"}]}

现在返回JSON："""

        user_prompt = f"用户需求: {user_input}\n返回JSON："

        try:
            response = ollama_chat([{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}], timeout=60)
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                plan = json.loads(json_match.group())
                return plan.get("steps", [])
        except:
            pass

        return [{"step": 1, "tool": "smart", "params": {"message": user_input}, "reason": "通用处理"}]

    def execute(self, user_input, context=""):
        steps = self.plan(user_input, context)
        if not steps:
            return {"ok": False, "error": "无法理解任务"}

        results = []
        for step in steps[:self.max_steps]:
            tool_name = step.get("tool", "")
            params = step.get("params", {})
            reason = step.get("reason", "")

            tool = self.tools.get(tool_name)
            if not tool:
                results.append({"step": step.get("step", 0), "tool": tool_name, "ok": False, "error": "工具不存在", "reason": reason})
                continue

            result = tool.execute(params)
            if not result.get("ok"):
                result = tool.execute(params)
            
            results.append({"step": step.get("step", 0), "tool": tool_name, "ok": result.get("ok", False), "result": result, "reason": reason})

        try:
            summary = ollama_chat([{"role": "user", "content": f"用户需求: {user_input}\n执行结果: {json.dumps(results, ensure_ascii=False)}\n请用简洁语言总结。"}], timeout=30)
        except:
            summary = "任务执行完成。"

        return {"ok": True, "user_input": user_input, "steps_count": len(results), "steps": results, "summary": summary}


agent = Agent()