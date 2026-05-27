"""加密 API"""
from server.services.crypto_chat import crypto_chat


def handle(body):
    action = body.get("action", "generate")

    if action == "generate":
        return crypto_chat.generate_keypair(body.get("user_id", "default"))

    if action == "encrypt":
        result = crypto_chat.encrypt_message(
            body.get("sender", ""),
            body.get("recipient", ""),
            body.get("message", ""),
        )
        return {"ok": result is not None, "encrypted": result}

    if action == "decrypt":
        result = crypto_chat.decrypt_message(
            body.get("recipient", ""),
            body.get("sender", ""),
            body.get("message", ""),
        )
        return {"ok": result is not None, "decrypted": result}

    if action == "biometric":
        return {
            "ok": crypto_chat.biometric_check(
                body.get("user_id", "default"),
                body.get("biometric_hash", ""),
            )
        }

    if action == "breach":
        return crypto_chat.data_breach_check(body.get("email", ""))

    if action == "audit":
        return crypto_chat.security_audit()

    return {"ok": False, "error": f"未知操作: {action}"}