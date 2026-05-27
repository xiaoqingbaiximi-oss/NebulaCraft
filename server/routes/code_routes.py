"""编程助手 API"""
from server.services.code_engine import code_engine


def handle(body):
    action = body.get("action", "complete")
    code = body.get("code", "")
    language = body.get("language", "python")

    actions = {
        "complete": lambda: code_engine.complete_code(code, language),
        "bugs": lambda: code_engine.find_bugs(code, language),
        "architecture": lambda: code_engine.architecture_review(body.get("description", ""), body.get("tech_stack", "")),
        "review": lambda: code_engine.code_review(code, language),
        "refactor": lambda: code_engine.refactor_suggestion(code, language),
        "tests": lambda: code_engine.generate_tests(code, language),
        "explain": lambda: code_engine.explain_code(code, language),
    }

    h = actions.get(action)
    return h() if h else {"ok": False, "error": f"未知操作: {action}"}