"""更新检查 API"""
from server.services.updater import updater


def handle(body):
    return updater.check()