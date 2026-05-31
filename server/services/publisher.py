# -*- coding: utf-8 -*-
"""
一键打包发布引擎
自动打包 EXE + 创建 GitHub Release
"""
import os
import re
import json
import subprocess
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))


def auto_publish(version=None):
    """自动打包发布"""
    steps = []
    
    # 1. 获取版本号
    config_path = os.path.join(BASE_DIR, "server", "config.py")
    with open(config_path, "r", encoding="utf-8") as f:
        config_content = f.read()
    
    version_match = re.search(r'VERSION\s*=\s*"([^"]+)"', config_content)
    current_version = version_match.group(1) if version_match else "0.0.0"
    
    if version:
        # 更新版本号
        new_config = re.sub(r'(VERSION\s*=\s*)"[^"]*"', rf'\1"{version}"', config_content)
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(new_config)
        current_version = version
        steps.append({"step": "更新版本号", "result": f"v{current_version}"})
    
    # 2. 打包 EXE
    try:
        result = subprocess.run(
            ["pyinstaller", "NebulaCraft.spec", "--clean"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            timeout=300
        )
        if result.returncode == 0:
            steps.append({"step": "打包 EXE", "result": "成功"})
        else:
            steps.append({"step": "打包 EXE", "result": f"失败: {result.stderr[-200:]}"})
            return {"ok": False, "steps": steps, "error": "打包失败"}
    except Exception as e:
        return {"ok": False, "steps": steps, "error": str(e)}
    
    # 3. 检查产物
    exe_path = os.path.join(BASE_DIR, "dist", "NebulaCraft.exe")
    if os.path.exists(exe_path):
        size_mb = os.path.getsize(exe_path) / 1024 / 1024
        steps.append({"step": "检查产物", "result": f"{size_mb:.1f}MB"})
    else:
        steps.append({"step": "检查产物", "result": "文件不存在"})
        return {"ok": False, "steps": steps, "error": "EXE 未生成"}
    
    return {
        "ok": True,
        "version": current_version,
        "steps": steps,
        "exe_path": exe_path,
        "message": f"✅ 打包完成 v{current_version}，请手动上传到 GitHub Release"
    }