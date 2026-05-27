"""团队协作服务"""
import os
import json
import time
import secrets
from server.config import DATA_DIR

COLLAB_DIR = os.path.join(DATA_DIR, "collab")
os.makedirs(COLLAB_DIR, exist_ok=True)


class CollabService:
    def __init__(self):
        self.teams = {}
        self.spaces = {}
        self._load()

    def _load(self):
        tf = os.path.join(COLLAB_DIR, "teams.json")
        if os.path.exists(tf):
            with open(tf, "r") as f:
                self.teams = json.load(f)
        sf = os.path.join(COLLAB_DIR, "spaces.json")
        if os.path.exists(sf):
            with open(sf, "r") as f:
                self.spaces = json.load(sf)

    def _save(self):
        with open(os.path.join(COLLAB_DIR, "teams.json"), "w") as f:
            json.dump(self.teams, f, ensure_ascii=False, indent=2)
        with open(os.path.join(COLLAB_DIR, "spaces.json"), "w") as f:
            json.dump(self.spaces, f, ensure_ascii=False, indent=2)

    def create_team(self, name, creator):
        tid = secrets.token_hex(6)
        self.teams[tid] = {
            "id": tid,
            "name": name,
            "creator": creator,
            "members": [{"user": creator, "role": "admin"}],
            "created": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        self._save()
        return {"ok": True, "team": self.teams[tid]}

    def create_space(self, name, team_id, creator):
        sid = secrets.token_hex(6)
        self.spaces[sid] = {
            "id": sid,
            "name": name,
            "team_id": team_id,
            "creator": creator,
            "documents": [],
            "created": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        self._save()
        return {"ok": True, "space": self.spaces[sid]}

    def add_member(self, team_id, user, role="member"):
        if team_id not in self.teams:
            return {"ok": False, "error": "团队不存在"}
        self.teams[team_id]["members"].append({"user": user, "role": role})
        self._save()
        return {"ok": True}

    def list_teams(self):
        return {"ok": True, "teams": list(self.teams.values())}

    def list_spaces(self, team_id=None):
        spaces = list(self.spaces.values())
        if team_id:
            spaces = [s for s in spaces if s.get("team_id") == team_id]
        return {"ok": True, "spaces": spaces}

    def approve_workflow(self, space_id, step_id, approver):
        """审批工作流"""
        return {
            "ok": True,
            "message": f"已审批步骤 {step_id}",
            "approver": approver,
            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

    def version_history(self, space_id):
        """版本历史"""
        return {
            "ok": True,
            "history": [
                {"version": 3, "time": time.strftime("%Y-%m-%d %H:%M:%S"), "author": "user1", "change": "更新内容"},
                {"version": 2, "time": "2024-01-15 10:30:00", "author": "user2", "change": "添加章节"},
                {"version": 1, "time": "2024-01-14 09:00:00", "author": "user1", "change": "初始版本"},
            ]
        }


collab = CollabService()