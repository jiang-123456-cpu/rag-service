from pydantic import BaseModel, Field, field_validator
from typing import Annotated
import re


class RegisterUser(BaseModel):
    # username：5-10字符，必须同时包含英文字母+数字，大小写不限
    username: Annotated[
        str,
        Field(
            min_length=5,
            max_length=10,
            description="用户名5-10位，必须同时包含英文和数字，仅允许英文、数字",
            examples=["Jiang123", "chen66"],
        ),
    ]

    # QQ邮箱规则：5~11位数字@qq.com
    email: Annotated[
        str,
        Field(
            pattern=r"^\d{5,11}@qq\.com$",
            description="仅支持QQ邮箱，5~11位QQ号@qq.com",
            examples=["2509500763@qq.com"],
        ),
    ]

    # password：6-12字符，必须同时包含英文字母+数字，大小写不限
    password: Annotated[
        str,
        Field(
            min_length=6,
            max_length=12,
            description="密码6-12位，必须同时包含英文和数字，仅允许英文、数字",
            examples=["Abc12345", "Pass678"],
        ),
    ]

    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        # 检查是否只包含英文字母和数字
        if not re.match(r"^[a-zA-Z0-9]+$", v):
            raise ValueError("用户名只能包含英文字母和数字")
        # 检查是否同时包含英文字母和数字
        if not re.search(r"[a-zA-Z]", v):
            raise ValueError("用户名必须包含至少一个英文字母")
        if not re.search(r"\d", v):
            raise ValueError("用户名必须包含至少一个数字")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        # 检查是否只包含英文字母和数字
        if not re.match(r"^[a-zA-Z0-9]+$", v):
            raise ValueError("密码只能包含英文字母和数字")
        # 检查是否同时包含英文字母和数字
        if not re.search(r"[a-zA-Z]", v):
            raise ValueError("密码必须包含至少一个英文字母")
        if not re.search(r"\d", v):
            raise ValueError("密码必须包含至少一个数字")
        return v


class LoginUser(BaseModel):
    username: Annotated[
        str,
        Field(
            min_length=5,
            max_length=10,
            description="用户名5-10位，必须同时包含英文和数字，仅允许英文、数字",
            examples=["Jiang123", "chen66"],
        ),
    ]
    password: Annotated[
        str,
        Field(
            min_length=6,
            max_length=12,
            description="密码6-12位，必须同时包含英文和数字，仅允许英文、数字",
            examples=["Abc12345", "Pass678"],
        ),
    ]

    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        # 同样的用户名校验
        if not re.match(r"^[a-zA-Z0-9]+$", v):
            raise ValueError("用户名只能包含英文字母和数字")
        if not re.search(r"[a-zA-Z]", v):
            raise ValueError("用户名必须包含至少一个英文字母")
        if not re.search(r"\d", v):
            raise ValueError("用户名必须包含至少一个数字")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        # 同样的密码校验
        if not re.match(r"^[a-zA-Z0-9]+$", v):
            raise ValueError("密码只能包含英文字母和数字")
        if not re.search(r"[a-zA-Z]", v):
            raise ValueError("密码必须包含至少一个英文字母")
        if not re.search(r"\d", v):
            raise ValueError("密码必须包含至少一个数字")
        return v


class DisabledUser(BaseModel):
    id: int = Field(..., ge=1, description="用户ID")
    # is_active: int = Field(ge=0, le=1, description="用户是否激活，0-禁用 1-激活")
