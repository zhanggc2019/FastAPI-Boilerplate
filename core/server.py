"""
服务器入口模块

此模块已被简化，所有应用初始化逻辑已移至 core/register.py
保留此文件仅为了向后兼容和作为应用实例的导出点
"""

from core.register import register_app

# 创建并导出应用实例
app = register_app()
