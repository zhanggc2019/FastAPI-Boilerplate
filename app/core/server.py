from fastapi import FastAPI

from app.core.register import register_app

# 默认导出一个可复用的应用实例
app = register_app()


def create_app() -> FastAPI:
    """创建新的 FastAPI 应用实例。"""
    return register_app()
