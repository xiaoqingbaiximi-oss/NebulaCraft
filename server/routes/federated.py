"""联邦学习 API"""
from server.services.federated import federated


def handle(body):
    action = body.get("action", "list_models")
    actions = {
        "list_models": lambda: federated.list_models(),
        "register_node": lambda: federated.register_node(body.get("name", ""), body.get("address", "")),
        "start_training": lambda: federated.start_training(body.get("model", ""), body.get("dataset", ""), body.get("epochs", 3)),
        "get_progress": lambda: federated.get_progress(body.get("job_id", "")),
        "compare_models": lambda: federated.compare_models(body.get("model_a", ""), body.get("model_b", ""), body.get("prompts", [])),
        "dataset_stats": lambda: federated.get_dataset_stats(),
    }
    h = actions.get(action)
    return h() if h else {"ok": False, "error": f"未知: {action}"}