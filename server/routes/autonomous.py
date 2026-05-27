"""自主代理 API"""
from server.services.autonomous import autonomous


def handle(body):
    action = body.get("action", "create")
    if action == "create": return autonomous.create_agent(body.get("name", ""), body.get("goal", ""), body.get("tools"))
    if action == "task": return autonomous.assign_task(body.get("agent_id", ""), body.get("task", ""))
    if action == "execute": return autonomous.execute_step(body.get("task_id", ""))
    if action == "reflect": return autonomous.reflect(body.get("task_id", ""))
    if action == "collaborate": return autonomous.collaborate(body.get("agents", []), body.get("goal", ""))
    return {"ok": False, "error": f"未知: {action}"}