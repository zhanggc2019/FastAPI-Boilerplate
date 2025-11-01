#!/usr/bin/env python3
"""
JWT密钥生成脚本
用于生成安全的JWT密钥
"""

import secrets
import string
import argparse


def generate_jwt_key(length: int = 64) -> str:
    """生成安全的JWT密钥"""
    # 使用字母、数字和特殊字符
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def main():
    parser = argparse.ArgumentParser(description="生成JWT密钥")
    parser.add_argument(
        "--length",
        type=int,
        default=64,
        help="密钥长度 (默认: 64)"
    )
    parser.add_argument(
        "--output",
        choices=["env", "raw"],
        default="env",
        help="输出格式 (env: 环境变量格式, raw: 纯文本)"
    )

    args = parser.parse_args()

    key = generate_jwt_key(args.length)

    if args.output == "env":
        print(f"JWT_SECRET_KEY={key}")
    else:
        print(key)


if __name__ == "__main__":
    main()
