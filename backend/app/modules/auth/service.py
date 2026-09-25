from app.modules.auth.models import Users
from app.modules.auth.repository import UserRepository
from app.modules.auth.schemas import UserCreate

from app.core.security import hash_password , verify_password , create_access_token


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

        hashed_password = await hash_password(user_data.password)

        user = Users(
            name=user_data.name,
            email=user_data.email,
            password_hash=hashed_password,
            role="field_representative",
            phone=user_data.phone
        )

        return await self.repository.create(user)

    async def login_user(self , email:str , password:str):
        user =await self.repository.get_by_email(email)

        if user is None:
            return None

        password_valid =await verify_password(password , user.password_hash)

        if not password_valid:
            return None

        if not user.is_active:
            return None

        access_token =create_access_token(user.id)

        return{
            "access_token":access_token,
            "token_type":"bearer"
        }