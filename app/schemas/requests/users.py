# pylint: disable=all

import re
from typing import Annotated

from pydantic import BaseModel, EmailStr, StringConstraints, field_validator


class RegisterUserRequest(BaseModel):
    email: EmailStr
    password: Annotated[str, StringConstraints(min_length=8, max_length=64)]
    username: Annotated[str, StringConstraints(min_length=3, max_length=64)]

    @field_validator("password")
    @classmethod
    def password_must_contain_special_characters(cls, v):
        if not re.search(r"[^a-zA-Z0-9]", v):
            raise ValueError("密码必须包含特殊字符")
        return v

    @field_validator("password")
    @classmethod
    def password_must_contain_numbers(cls, v):
        if not re.search(r"[0-9]", v):
            raise ValueError("密码必须包含数字")
        return v

    @field_validator("password")
    @classmethod
    def password_must_contain_uppercase(cls, v):
        if not re.search(r"[A-Z]", v):
            raise ValueError("密码必须包含大写字母")
        return v

    @field_validator("password")
    @classmethod
    def password_must_contain_lowercase(cls, v):
        if not re.search(r"[a-z]", v):
            raise ValueError("密码必须包含小写字母")
        return v

    @field_validator("username")
    @classmethod
    def username_must_not_contain_special_characters(cls, v):
        # 允许字母、数字、下划线和连字符
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError("用户名只能包含字母、数字、下划线和连字符")
        return v


class LoginUserRequest(BaseModel):
    email: EmailStr
    password: str
