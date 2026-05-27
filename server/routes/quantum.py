"""量子 API"""
from server.services.quantum import quantum


def handle(body):
    action = body.get("action", "status")
    if action == "status": return quantum.get_status()
    if action == "key": return quantum.generate_quantum_key()
    if action == "random": return quantum.quantum_random(body.get("bits", 256))
    if action == "encrypt": return quantum.encrypt_post_quantum(body.get("message", ""), body.get("public_key", ""))
    return {"ok": False, "error": f"未知: {action}"}