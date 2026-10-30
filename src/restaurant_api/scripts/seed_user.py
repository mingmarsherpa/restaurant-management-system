import argparse
import asyncio
import getpass

from sqlalchemy import select

from ..database import AsyncSessionLocal
from ..models.user import Role, User
from ..services.auth import hash_password


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a restaurant staff user")
    parser.add_argument("--username", required=True)
    parser.add_argument("--email", required=True)
    parser.add_argument("--role", required=True, choices=[role.value for role in Role])
    return parser.parse_args()


async def seed_user(
    username: str,
    email: str,
    role: Role,
    password: str,
) -> None:
    async with AsyncSessionLocal() as session:
        existing = await session.scalar(
            select(User).where(
                (User.username == username) | (User.email == email)
            )
        )
        if existing is not None:
            raise ValueError("A user with that username or email already exists")

        session.add(
            User(
                username=username,
                email=email,
                hashed_password=hash_password(password),
                role=role,
            )
        )
        await session.commit()


def main() -> None:
    args = parse_args()
    password = getpass.getpass("Password: ")
    if not password:
        raise SystemExit("Password cannot be empty")
    try:
        asyncio.run(
            seed_user(
                username=args.username,
                email=args.email,
                role=Role(args.role),
                password=password,
            )
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    print(f"Created {args.role} user {args.username}")


if __name__ == "__main__":
    main()
