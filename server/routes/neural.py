"""神经接口 API"""
from server.services.neural import neural


def handle(body):
    action = body.get("action", "connect")
    if action == "connect": return neural.connect_device(body.get("type", ""), body.get("id", ""))
    if action == "session": return neural.start_session(body.get("type", "eeg"))
    if action == "metrics": return neural.get_metrics(body.get("session_id", ""))
    if action == "gesture": return neural.detect_gesture(body.get("landmarks", []))
    if action == "expression": return neural.analyze_expression(body.get("face", {}))
    return {"ok": False, "error": f"未知: {action}"}