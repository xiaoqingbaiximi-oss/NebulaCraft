"""Agent API 路由"""
import json
from server.services.agent import agent


def handle(body):
    user_input = body.get("message", "").strip()
    context = body.get("context", "")
    if not user_input:
        return {"ok": False, "error": "请输入任务描述"}
    return agent.execute(user_input, context)


def handle_plan(body):
    user_input = body.get("message", "").strip()
    steps = agent.plan(user_input)
    return {"ok": True, "steps": steps}


def handle_list_tools(body):
    tools = []
    for name, tool in agent.tools.items():
        tools.append({"name": name, "description": tool.description, "params": tool.params_schema})
    return {"ok": True, "tools": tools}