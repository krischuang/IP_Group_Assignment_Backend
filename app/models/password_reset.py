from datetime import datetime
from beanie import Document
from pydantic import EmailStr


class PasswordResetToken(Document):
    email: EmailStr
    token: str
    expires_at: datetime
    used: bool = False
    verified: bool = False

    class Settings:
        name = "password_reset_tokens"
