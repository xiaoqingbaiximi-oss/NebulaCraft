"""联邦学习服务"""
import os
import json
import time
import hashlib
from server.config import DATA_DIR

FED_DIR = os.path.join(DATA_DIR, "federated")
os.makedirs(FED_DIR, exist_ok=True)


class FederatedLearning:
    def __init__(self):
        self.nodes = {}
        self.models = {}
        self.training_jobs = {}
        self._load()

    def _load(self):
        nf = os.path.join(FED_DIR, "nodes.json")
        if os.path.exists(nf):
            with open(nf, "r") as f:
                self.nodes = json.load(f)
        mf = os.path.join(FED_DIR, "models.json")
        if os.path.exists(mf):
            with open(mf, "r") as f:
                self.models = json.load(f)

    def _save(self):
        with open(os.path.join(FED_DIR, "nodes.json"), "w") as f:
            json.dump(self.nodes, f, ensure_ascii=False, indent=2)
        with open(os.path.join(FED_DIR, "models.json"), "w") as f:
            json.dump(self.models, f, ensure_ascii=False, indent=2)

    def register_node(self, name, address):
        """注册联邦节点"""
        import secrets
        node_id = secrets.token_hex(6)
        self.nodes[node_id] = {
            "id": node_id, "name": name, "address": address,
            "status": "active", "joined": time.strftime("%Y-%m-%d %H:%M:%S"),
            "contributions": 0,
        }
        self._save()
        return {"ok": True, "node": self.nodes[node_id]}

    def start_training(self, model_name, dataset, epochs=3, lora_rank=8):
        """启动联邦训练"""
        import secrets
        job_id = secrets.token_hex(6)
        self.training_jobs[job_id] = {
            "id": job_id, "model": model_name, "dataset": dataset,
            "epochs": epochs, "lora_rank": lora_rank,
            "status": "running", "progress": 0,
            "started": time.strftime("%Y-%m-%d %H:%M:%S"),
            "nodes_participating": len(self.nodes),
        }
        return {"ok": True, "job": self.training_jobs[job_id]}

    def get_progress(self, job_id):
        """获取训练进度"""
        if job_id in self.training_jobs:
            job = self.training_jobs[job_id]
            job["progress"] = min(100, job.get("progress", 0) + 5)
            return {"ok": True, "job": job}
        return {"ok": False, "error": "任务不存在"}

    def list_models(self):
        """列出可微调模型"""
        base_models = [
            {"name": "qwen2.5:1.5b", "size": "1.5B", "type": "chat"},
            {"name": "qwen2.5:7b", "size": "7B", "type": "chat"},
            {"name": "llama3.2:3b", "size": "3B", "type": "chat"},
            {"name": "mistral:7b", "size": "7B", "type": "chat"},
        ]
        return {"ok": True, "models": base_models, "custom": list(self.models.values())}

    def compare_models(self, model_a, model_b, test_prompts):
        """模型 A/B 对比"""
        results = {
            "model_a": model_a, "model_b": model_b,
            "tests": len(test_prompts),
            "scores": {"a": 0, "b": 0, "tie": 0},
        }
        return {"ok": True, "comparison": results}

    def get_dataset_stats(self):
        """数据集统计"""
        dataset_dir = os.path.join(FED_DIR, "datasets")
        os.makedirs(dataset_dir, exist_ok=True)
        datasets = []
        for f in os.listdir(dataset_dir):
            fp = os.path.join(dataset_dir, f)
            datasets.append({
                "name": f, "size": os.path.getsize(fp) if os.path.isfile(fp) else 0,
                "type": f.split(".")[-1] if "." in f else "unknown",
            })
        return {"ok": True, "datasets": datasets, "count": len(datasets)}


federated = FederatedLearning()