"""元宇宙服务"""
import json
import time
import secrets


class Metaverse:
    def __init__(self):
        self.spaces = {}
        self.avatars = {}
        self.objects = {}

    def create_space(self, name, template="office"):
        """创建虚拟空间"""
        sid = secrets.token_hex(6)
        templates = {
            "office": {"walls": "glass", "floor": "wood", "lighting": "natural"},
            "garden": {"terrain": "grass", "sky": "sunset", "trees": "oak"},
            "lab": {"walls": "white", "equipment": "high-tech", "lighting": "led"},
        }
        self.spaces[sid] = {
            "id": sid, "name": name,
            "template": templates.get(template, templates["office"]),
            "users": [], "objects": [],
            "created": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        return {"ok": True, "space": self.spaces[sid]}

    def create_avatar(self, name, style="anime"):
        """创建虚拟形象"""
        aid = secrets.token_hex(6)
        self.avatars[aid] = {
            "id": aid, "name": name, "style": style,
            "position": {"x": 0, "y": 0, "z": 0},
            "animation": "idle",
            "expressions": ["smile", "wave", "think"],
        }
        return {"ok": True, "avatar": self.avatars[aid]}

    def add_object(self, space_id, obj_type, position):
        """添加3D对象"""
        oid = secrets.token_hex(4)
        obj = {"id": oid, "type": obj_type, "position": position,
               "interactive": True}
        if space_id in self.spaces:
            self.spaces[space_id]["objects"].append(obj)
        return {"ok": True, "object": obj}

    def spatial_audio(self, source_pos, listener_pos):
        """空间音频计算"""
        dx = source_pos.get("x", 0) - listener_pos.get("x", 0)
        dy = source_pos.get("y", 0) - listener_pos.get("y", 0)
        dz = source_pos.get("z", 0) - listener_pos.get("z", 0)
        distance = (dx**2 + dy**2 + dz**2) ** 0.5
        return {
            "ok": True,
            "pan": max(-1, min(1, dx / max(distance, 1))),
            "volume": max(0, 1 - distance / 100),
            "distance": round(distance, 2),
        }

    def digital_twin(self, user_id, data):
        """数字孪生"""
        return {
            "ok": True,
            "twin": {
                "user": user_id,
                "mirror": {
                    "preferences": data.get("preferences", {}),
                    "history": data.get("history", []),
                    "predictions": ["明天可能想搜索AI相关话题"],
                }
            }
        }


metaverse = Metaverse()