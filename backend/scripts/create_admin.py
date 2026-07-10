"""Bootstrap CLI: 创建首位管理员账号。

使用方式：
    cd ui/backend
    python scripts/create_admin.py --phone 13800138000

脚本会在终端打印 TOTP 二维码 ASCII 图，用 Google 身份验证器扫码后，
访问前端 /login 页面，输入手机号 + 当前动态码登录。

幂等：如果该手机号已存在 admin 用户，会复用其 TOTP secret 并重新打印二维码；
如果是已存在的非 admin 用户，会升级为 admin。
"""

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import qrcode

from app.auth.security import build_totp_uri, generate_totp_secret
from app.database import async_session, init_db
from app.models import User


async def main(phone: str) -> None:
    await init_db()
    async with async_session() as db:
        result = await db.execute(User.__table__.select().where(User.phone == phone))
        existing = result.first()
        if existing:
            if existing.role != "admin":
                await db.execute(
                    User.__table__.update()
                    .where(User.phone == phone)
                    .values(role="admin")
                )
                await db.commit()
                print(f"[upgrade] 已将手机号 {phone} 升级为 admin")
            secret = existing.totp_secret or generate_totp_secret()
            if not existing.totp_secret:
                await db.execute(
                    User.__table__.update()
                    .where(User.phone == phone)
                    .values(totp_secret=secret, is_active=True)
                )
                await db.commit()
                print(f"[upgrade] 已为 {phone} 生成新的 TOTP secret")
            else:
                print(f"[info] 手机号 {phone} 已是 admin，复用既有 TOTP secret")
        else:
            secret = generate_totp_secret()
            user = User(
                phone=phone,
                role="admin",
                totp_secret=secret,
                is_active=True,
                enrolled_at=None,
            )
            db.add(user)
            await db.commit()
            print(f"[created] 已创建 admin 用户：{phone}")

        # 重新读取以拿到最新 secret
        result = await db.execute(User.__table__.select().where(User.phone == phone))
        row = result.first()
        secret = row.totp_secret

    uri = build_totp_uri(phone, secret)
    print()
    print("=" * 60)
    print("用 Google 身份验证器扫码：")
    print("=" * 60)
    qr = qrcode.QRCode(border=1)
    qr.add_data(uri)
    qr.make(fit=True)
    qr.print_ascii(invert=True)
    print()
    print("无法扫码？手动添加：")
    print(f"  账号名: {phone}")
    print(f"  密钥:   {secret}")
    print("  类型:   基于时间 (TOTP)")
    print()
    print("扫码完成后，访问前端 /login 页面登录。")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="创建首位 admin 账号")
    parser.add_argument("--phone", required=True, help="管理员手机号，例如 13800138000")
    args = parser.parse_args()
    asyncio.run(main(args.phone))
