# -*- coding: utf-8 -*-
"""
系统监控引擎
CPU、内存、磁盘、进程监控
"""
import os
import json
import time
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
MONITOR_FILE = os.path.join(DATA_DIR, "system_monitor.json")


def get_system_info():
    """获取系统信息"""
    info = {
        "time": datetime.now().isoformat(),
        "cpu_percent": None,
        "memory": {},
        "disk": {},
        "uptime": None
    }
    
    # CPU
    try:
        import psutil
        info["cpu_percent"] = psutil.cpu_percent(interval=0.5)
        info["cpu_count"] = psutil.cpu_count()
        
        mem = psutil.virtual_memory()
        info["memory"] = {
            "total_gb": round(mem.total / 1024**3, 1),
            "used_gb": round(mem.used / 1024**3, 1),
            "percent": mem.percent
        }
        
        disk = psutil.disk_usage('/')
        info["disk"] = {
            "total_gb": round(disk.total / 1024**3, 1),
            "used_gb": round(disk.used / 1024**3, 1),
            "percent": disk.percent
        }
        
        boot = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot
        info["uptime"] = str(uptime).split('.')[0]
        
    except ImportError:
        info["error"] = "psutil 未安装，运行: pip install psutil"
    except Exception as e:
        info["error"] = str(e)
    
    return {"ok": True, "info": info}


def get_top_processes(limit=10):
    """获取占用最高的进程"""
    try:
        import psutil
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                processes.append(proc.info)
            except:
                pass
        
        processes.sort(key=lambda x: x.get('cpu_percent', 0), reverse=True)
        return {"ok": True, "processes": processes[:limit]}
    except ImportError:
        return {"ok": False, "error": "psutil 未安装"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def ai_system_operation(user_message):
    """AI 处理系统监控请求"""
    msg = user_message.lower()
    
    if any(w in msg for w in ["系统信息", "cpu", "内存", "磁盘", "系统状态"]):
        return get_system_info()
    
    if any(w in msg for w in ["进程", "任务管理器", "什么在运行", "占用"]):
        return get_top_processes()
    
    return {"ok": False, "error": "不涉及系统监控"}