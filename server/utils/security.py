import os
import re

def safe_path(base_dir, user_path):
    user_path = user_path.split("?")[0].split("#")[0]
    full = os.path.normpath(os.path.join(base_dir, user_path.lstrip("/")))
    base_real = os.path.normpath(base_dir)
    if not full.startswith(base_real):
        return None
    return full

def sanitize_filename(filename):
    safe = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
    if not safe or safe.startswith('.'):
        import secrets
        safe = f"file_{secrets.token_hex(4)}"
    return safe