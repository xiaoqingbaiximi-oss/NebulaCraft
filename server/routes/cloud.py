"""云端模型 API"""
from server.services.cloud_ai import cloud_ai


def handle(body):
    return cloud_ai.get_status()