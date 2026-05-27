"""
定时任务调度器
支持: 定时 AI 任务 / 周期执行
"""
import json
import time
import threading
import os
from datetime import datetime, timedelta
from server.config import DATA_DIR

SCHEDULE_FILE = os.path.join(DATA_DIR, "schedules.json")
_schedules = []
_lock = threading.Lock()
_running = False


def _load():
    global _schedules
    try:
        if os.path.exists(SCHEDULE_FILE):
            with open(SCHEDULE_FILE, "r", encoding="utf-8") as f:
                _schedules = json.load(f)
    except:
        _schedules = []


def _save():
    with open(SCHEDULE_FILE, "w", encoding="utf-8") as f:
        json.dump(_schedules, f, ensure_ascii=False, indent=2)


def _execute_task(task):
    """执行定时任务"""
    from server.services.ollama import chat
    try:
        prompt = task.get("prompt", "")
        model = task.get("model", "")
        result = chat([{"role": "user", "content": prompt}], model=model, timeout=120)
        task["last_result"] = result
        task["last_run"] = datetime.now().isoformat()
        _save()
        print(f"[Scheduler] Task '{task.get('name','')}' completed")
    except Exception as e:
        print(f"[Scheduler] Task failed: {e}")


def _checker():
    """后台检查线程"""
    global _running
    while _running:
        now = datetime.now()
        with _lock:
            for task in _schedules:
                if not task.get("enabled", True):
                    continue
                # 检查是否到执行时间
                schedule_time = task.get("schedule_time", "")
                interval = task.get("interval_minutes", 0)

                if interval > 0:
                    last_run = task.get("last_run", "")
                    if last_run:
                        last_dt = datetime.fromisoformat(last_run)
                        if (now - last_dt).total_seconds() < interval * 60:
                            continue

                if schedule_time:
                    try:
                        target = datetime.strptime(schedule_time, "%H:%M").time()
                        if now.time().hour != target.hour or now.time().minute != target.minute:
                            continue
                    except:
                        pass

                # 避免同一分钟重复执行
                last_run = task.get("last_run", "")
                if last_run:
                    last_dt = datetime.fromisoformat(last_run)
                    if (now - last_dt).total_seconds() < 60:
                        continue

                threading.Thread(target=_execute_task, args=(task,), daemon=True).start()

        time.sleep(30)  # 每30秒检查一次


def start_scheduler():
    global _running
    _load()
    if not _running:
        _running = True
        t = threading.Thread(target=_checker, daemon=True)
        t.start()
        print("[Scheduler] Started")


def stop_scheduler():
    global _running
    _running = False


def add_schedule(name, prompt, schedule_time=None, interval_minutes=0, model=""):
    with _lock:
        task = {
            "id": str(int(time.time() * 1000)),
            "name": name,
            "prompt": prompt,
            "schedule_time": schedule_time,
            "interval_minutes": interval_minutes,
            "model": model,
            "enabled": True,
            "created": datetime.now().isoformat(),
            "last_run": None,
            "last_result": None,
        }
        _schedules.append(task)
        _save()
    return {"ok": True, "task": task}


def list_schedules():
    return {"ok": True, "schedules": _schedules}


def delete_schedule(task_id):
    global _schedules
    with _lock:
        _schedules = [t for t in _schedules if t.get("id") != task_id]
        _save()
    return {"ok": True}


def toggle_schedule(task_id):
    global _schedules
    with _lock:
        for t in _schedules:
            if t.get("id") == task_id:
                t["enabled"] = not t.get("enabled", True)
        _save()
    return {"ok": True}