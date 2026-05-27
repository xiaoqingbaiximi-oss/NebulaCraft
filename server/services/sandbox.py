"""
安全代码执行沙箱 - 子进程隔离 + 资源限制 + 危险操作检测
"""
import subprocess
import tempfile
import os
import signal
import re
import sys

# 危险模式黑名单
FORBIDDEN_PATTERNS = [
    r'os\.system\s*\(',
    r'subprocess\.',
    r'__import__\s*\(',
    r'eval\s*\(',
    r'exec\s*\(',
    r'open\s*\([^)]*[\'"]w',
    r'shutil\.',
    r'os\.remove\s*\(',
    r'os\.unlink\s*\(',
    r'os\.rmdir\s*\(',
    r'os\.chmod\s*\(',
    r'os\.chown\s*\(',
    r'ctypes\.',
    r'\._module',
    r'globals\s*\(\s*\)',
    r'locals\s*\(\s*\)',
    r'getattr\s*\([^)]*[\'"]__',
    r'setattr\s*\(',
    r'delattr\s*\(',
    r'compile\s*\(',
    r'breakpoint\s*\(',
]

# 允许的安全内置函数
SAFE_BUILTINS = {
    'abs': abs, 'all': all, 'any': any, 'bin': bin, 'bool': bool,
    'chr': chr, 'complex': complex, 'dict': dict, 'divmod': divmod,
    'enumerate': enumerate, 'filter': filter, 'float': float, 'format': format,
    'frozenset': frozenset, 'hex': hex, 'int': int, 'isinstance': isinstance,
    'issubclass': issubclass, 'iter': iter, 'len': len, 'list': list,
    'map': map, 'max': max, 'min': min, 'next': next, 'oct': oct,
    'ord': ord, 'pow': pow, 'print': print, 'range': range, 'repr': repr,
    'reversed': reversed, 'round': round, 'set': set, 'slice': slice,
    'sorted': sorted, 'str': str, 'sum': sum, 'tuple': tuple, 'type': type,
    'zip': zip, 'hash': hash, 'id': id, 'input': input, 'bytes': bytes,
    'bytearray': bytearray,
}

# 允许导入的安全模块
SAFE_MODULES = {
    'math', 'cmath', 'decimal', 'fractions', 'random',
    'datetime', 'time', 'calendar',
    'collections', 'itertools', 'functools', 'operator',
    'json', 'csv', 're', 'string', 'textwrap',
    'statistics', 'dataclasses', 'typing', 'enum',
    'copy', 'pprint', 'hashlib', 'base64', 'uuid',
    'unicodedata', 'difflib',
}


def check_code_safety(code: str) -> tuple[bool, str]:
    """检查代码是否包含危险操作"""
    # 检查危险模式
    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, code, re.IGNORECASE):
            return False, f"检测到危险操作: {pattern}"
    
    # 检查是否尝试导入危险模块
    import_pattern = re.findall(r'(?:from\s+(\S+)\s+import|import\s+(\S+))', code)
    for groups in import_pattern:
        module_name = groups[0] or groups[1]
        base_module = module_name.split('.')[0]
        if base_module not in SAFE_MODULES:
            return False, f"不允许导入模块: {base_module}"
    
    return True, ""


def execute(code: str, timeout: int = 5, memory_limit_mb: int = 128) -> dict:
    """安全执行 Python 代码"""
    
    # 拒绝空代码
    if not code or not code.strip():
        return {"ok": False, "error": "代码不能为空", "output": ""}
    
    # 代码长度限制
    if len(code) > 10000:
        return {"ok": False, "error": "代码过长，最大10000字符", "output": ""}
    
    # 安全检查
    safe, error = check_code_safety(code)
    if not safe:
        return {"ok": False, "error": error, "output": ""}
    
    """在隔离子进程中执行 Python 代码"""
    
    # 安全检查
    safe, error = check_code_safety(code)
    if not safe:
        return {"ok": False, "error": error, "output": ""}
    
    # 构建执行脚本
    execution_code = f'''
import sys
import signal
import resource
import traceback
import io
from contextlib import redirect_stdout, redirect_stderr

# 设置内存限制
try:
    resource.setrlimit(resource.RLIMIT_AS, ({memory_limit_mb} * 1024 * 1024, -1))
except:
    pass

# 设置CPU时间限制
try:
    resource.setrlimit(resource.RLIMIT_CPU, ({timeout}, {timeout} + 1))
except:
    pass

# 限制内置函数
safe_builtins = {SAFE_BUILTINS}
safe_builtins['__builtins__'] = safe_builtins

# 白名单模块
import math, json, re, random, datetime, collections, itertools, functools, statistics, copy

# 执行用户代码
stdout_buf = io.StringIO()
stderr_buf = io.StringIO()

result = None
try:
    with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
        exec("""
{code}
""", {{"__builtins__": safe_builtins, "math": math, "json": json, "re": re, "random": random, "datetime": datetime, "collections": collections, "itertools": itertools, "functools": functools, "statistics": statistics, "copy": copy}})
except SystemExit:
    pass
except Exception as e:
    print(f"Error: {{type(e).__name__}}: {{e}}", file=sys.stderr)

output = stdout_buf.getvalue()
errors = stderr_buf.getvalue()

print("__RESULT_SPLIT__")
print("__STDOUT__")
print(output)
print("__STDERR__")
print(errors)
'''

    try:
        # 写入临时文件
        tmp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8')
        tmp_file.write(execution_code)
        tmp_file.close()
        
        # 在子进程中执行
        process = subprocess.Popen(
            [sys.executable, '-u', tmp_file.name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            preexec_fn=os.setsid if hasattr(os, 'setsid') else None
        )
        
        try:
            stdout, stderr = process.communicate(timeout=timeout + 2)
        except subprocess.TimeoutExpired:
            os.killpg(os.getpgid(process.pid), signal.SIGKILL) if hasattr(os, 'killpg') else process.kill()
            return {"ok": False, "error": f"代码执行超时 ({timeout}秒)", "output": ""}
        finally:
            os.unlink(tmp_file.name)
        
        # 解析输出
        output = ""
        errors = ""
        if "__STDOUT__" in stdout:
            parts = stdout.split("__STDOUT__")
            if len(parts) > 1:
                stderr_parts = parts[1].split("__STDERR__")
                output = stderr_parts[0].strip()
                if len(stderr_parts) > 1:
                    errors = stderr_parts[1].strip()
        else:
            output = stdout
        
        if stderr:
            errors = (errors + "\n" + stderr).strip()
        
        return {
            "ok": True,
            "output": output,
            "errors": errors,
            "return_code": process.returncode
        }
        
    except Exception as e:
        return {"ok": False, "error": str(e), "output": ""}