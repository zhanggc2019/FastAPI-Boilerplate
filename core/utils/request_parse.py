from fastapi import Request
from user_agents import parse

from core.common.dataclasses import UserAgentInfo


def get_request_ip(request: Request) -> str:
    """
    获取请求的 IP 地址

    :param request: FastAPI 请求对象
    :return:
    """
    real = request.headers.get("X-Real-IP")
    if real:
        return real

    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0]

    # 忽略 pytest
    if request.client and request.client.host == "testclient":
        return "127.0.0.1"
    return request.client.host if request.client else "127.0.0.1"


async def parse_ip_info(request: Request) -> str | None:
    """
    解析请求的 IP 信息

    :param request: FastAPI 请求对象
    :return:
    """
    ip = get_request_ip(request)
    return ip


def parse_user_agent_info(request: Request) -> UserAgentInfo:
    """
    解析请求的用户代理信息

    :param request: FastAPI 请求对象
    :return:
    """
    user_agent = request.headers.get("User-Agent")
    user_agent_ = parse(user_agent)
    os = user_agent_.get_os()
    browser = user_agent_.get_browser()
    device = user_agent_.get_device()
    return UserAgentInfo(user_agent=user_agent, device=device, os=os, browser=browser)
