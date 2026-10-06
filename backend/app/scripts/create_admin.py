import asyncio
from sqlalchemy import select
from app.core.config import settings
from app.core.security import hash_password
from app.db.database import SessionLocal
from app.modules.auth.models import Users


async def create_admin():
    async with SessionLocal() as session:

        # Check whether an admin already exists
        admin_result = await session.execute(
            select(Users).where(Users.role == "admin")
        )

        existing_admin = admin_result.scalar_one_or_none()

        if existing_admin is not None:
            print("Admin already exists.")
            return

        # Check whether the configured bootstrap user already exists
        user_result = await session.execute(
            select(Users).where(
                Users.email == settings.INITIAL_ADMIN_EMAIL
            )
        )

        existing_user = user_result.scalar_one_or_none()

        if existing_user is not None:
            existing_user.role = "admin"
            existing_user.is_active = True

            await session.commit()

            print("Existing bootstrap user restored as admin.")
            return

        # Create a new admin if bootstrap user does not exist
        admin = Users(
            name=settings.INITIAL_ADMIN_NAME,
            email=settings.INITIAL_ADMIN_EMAIL,
            password_hash=await hash_password(
                settings.INITIAL_ADMIN_PASSWORD
            ),
            role="admin",
            is_active=True,
        )

        session.add(admin)

        await session.commit()

        print("Initial admin created successfully.")


if __name__ == "__main__":
    asyncio.run(create_admin())

# python -m app.scripts.create_admin