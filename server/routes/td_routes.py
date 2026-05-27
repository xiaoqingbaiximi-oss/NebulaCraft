"""
3D生成 API 路由
"""
import json
import uuid
from server.services.td_engine import td_engine

def handle_3d_generate(handler, body: dict) -> dict:
    task_id = body.get("task_id", str(uuid.uuid4())[:8])
    prompt = body.get("prompt", "")
    image_base64 = body.get("image_base64", "")
    if image_base64:
        return td_engine.image_to_3d(image_base64, task_id)
    elif prompt:
        return td_engine.text_to_3d(prompt, task_id)
    else:
        return {"ok": False, "error": "Provide prompt or image_base64"}

def handle_3d_download(handler, task_id: str):
    model_path = td_engine.get_model_file(task_id)
    if not model_path:
        handler._send_json({"ok": False, "error": "Model file not found"}, 404)
        return
    handler.send_response(200)
    handler.send_header("Content-Type", "model/gltf-binary")
    handler.send_header("Content-Disposition", 'attachment; filename="model.glb"')
    handler.send_header("Content-Length", str(model_path.stat().st_size))
    handler.end_headers()
    with open(model_path, "rb") as f:
        handler.wfile.write(f.read())