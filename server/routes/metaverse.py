"""元宇宙 API"""
from server.services.metaverse import metaverse


def handle(body):
    action = body.get("action", "space")
    if action == "space": return metaverse.create_space(body.get("name", ""), body.get("template", "office"))
    if action == "avatar": return metaverse.create_avatar(body.get("name", ""), body.get("style", "anime"))
    if action == "object": return metaverse.add_object(body.get("space_id", ""), body.get("type", ""), body.get("position", {}))
    if action == "audio": return metaverse.spatial_audio(body.get("source", {}), body.get("listener", {}))
    if action == "twin": return metaverse.digital_twin(body.get("user_id", ""), body.get("data", {}))
    return {"ok": False, "error": f"未知: {action}"}