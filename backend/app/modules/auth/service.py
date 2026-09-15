from pwdlib import PasswordHash

from app.modules.auth.models import Users
from app.modules.auth.repository import UserRepository
from app.modules.auth.schemas import UserCreate


password_hash = PasswordHash.recommended()


class UserService:

    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def get_all_users(self):
        return await self.repository.get_all()

    async def get_user_by_id(self, user_id: int):
        return await self.repository.get_by_id(user_id)

    async def create_user(self, user_data: UserCreate):

        existing_user = await self.repository.get_by_email(
            user_data.email
        )

        if existing_user is not None:
            return None

        hashed_password = password_hash.hash(
            user_data.password
        )

        user = Users(
            name=user_data.name,
            email=user_data.email,
            password_hash=hashed_password,
            role=user_data.role,
            phone=user_data.phone
        )

        return await self.repository.create(user)