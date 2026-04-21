from datetime import datetime
from enum import Enum
from beanie import Document
from pydantic import EmailStr


class UserRole(str, Enum):
    admin = "Admin"
    user = "User"


class User(Document):
    user_id: int
    email: EmailStr
    password: str
    full_name: str
    role: UserRole = UserRole.user
    bio: str | None = None
    image_address: str | None = None
    create_time: datetime
    update_time: datetime

    class Settings:
        name = "users"
