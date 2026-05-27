"""隧道 API"""
from server.services.tunnel import tunnel


def handle(body):
    action = body.get("action", "status")
    if action == "start":
        return tunnel.start_ngrok()
    return tunnel.status()