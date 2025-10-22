from httpx import AsyncClient

from tests.factory.users import create_fake_user


async def _create_user_and_login(client: AsyncClient, fake_user=None) -> None:
    """
    创建用户并登录

    Args:
        client: HTTP客户端
        fake_user: 假用户数据，如果为None则创建一个新用户
    """
    if fake_user is None:
        fake_user = create_fake_user()

    await client.post("/v1/users/", json=fake_user)

    response = await client.post("/v1/users/login", json=fake_user)
    access_token = response.json()["access_token"]

    client.headers.update({"Authorization": f"Bearer {access_token}"})

    return None


__all__ = ["_create_user_and_login"]
