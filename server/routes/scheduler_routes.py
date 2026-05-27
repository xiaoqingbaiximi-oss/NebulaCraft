"""
定时任务 API
"""
from server.services.scheduler import add_schedule, list_schedules, delete_schedule, toggle_schedule


def handle(body: dict) -> dict:
    action = body.get("action", "list")

    if action == "add":
        return add_schedule(
            name=body.get("name", ""),
            prompt=body.get("prompt", ""),
            schedule_time=body.get("schedule_time", ""),
            interval_minutes=int(body.get("interval_minutes", 0)),
            model=body.get("model", ""),
        )
    if action == "list":
        return list_schedules()
    if action == "delete":
        return delete_schedule(body.get("id", ""))
    if action == "toggle":
        return toggle_schedule(body.get("id", ""))

    return {"ok": False, "error": "Unknown action"}