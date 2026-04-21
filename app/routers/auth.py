from datetime import datetime, timedelta, timezone
from pymongo import ReturnDocument
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from jose import jwt
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from app.config import settings
from app.keys import public_key_pem
from app.models.user import User, UserRole
from app.models.counter import Counter
from app.utils.rsa_crypto import decrypt_password

router = APIRouter(prefix="/auth", tags=["auth"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class PublicKeyResponse(BaseModel):
    public_key: str


class RegisterRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    role: UserRole = UserRole.user


class RegisterResponse(BaseModel):
    user_id: int
    email: str
    full_name: str
    role: UserRole
    create_time: datetime
    update_time: datetime


async def _next_user_id() -> int:
    collection = Counter.get_motor_collection()
    result = await collection.find_one_and_update(
        {"name": "user_id"},
        {"$inc": {"value": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    return result["value"]


@router.get("/public-key", response_model=PublicKeyResponse)
def get_public_key():
    return PublicKeyResponse(public_key=public_key_pem)


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest):
    try:
        plain_password = decrypt_password(body.password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    existing = await User.find_one(User.email == body.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    now = datetime.now(timezone.utc)
    user = User(
        user_id=await _next_user_id(),
        email=body.email,
        password=pwd_context.hash(plain_password),
        full_name=body.full_name,
        role=body.role,
        create_time=now,
        update_time=now,
    )
    await user.insert()

    return RegisterResponse(
        user_id=user.user_id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        create_time=user.create_time,
        update_time=user.update_time,
    )


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: UserRole


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest):
    try:
        plain_password = decrypt_password(body.password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    user = await User.find_one(User.email == body.email)
    if not user or not pwd_context.verify(plain_password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    token = jwt.encode(
        {"sub": str(user.user_id), "email": user.email, "role": user.role, "exp": expire},
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )

    return LoginResponse(access_token=token, role=user.role)


_bearer = HTTPBearer()


class MeResponse(BaseModel):
    user_id: int
    email: str
    full_name: str
    role: UserRole
    bio: str | None
    image_address: str | None
    create_time: datetime
    update_time: datetime


@router.get("/me", response_model=MeResponse)
async def me(credentials: HTTPAuthorizationCredentials = Depends(_bearer)):
    try:
        payload = jwt.decode(credentials.credentials, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    user = await User.find_one(User.user_id == user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return MeResponse(
        user_id=user.user_id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        bio=user.bio,
        image_address=user.image_address,
        create_time=user.create_time,
        update_time=user.update_time,
    )


class UpdateMeRequest(BaseModel):
    full_name: str | None = None
    bio: str | None = None
    image_address: str | None = None


@router.post("/me", response_model=MeResponse)
async def update_me(body: UpdateMeRequest, credentials: HTTPAuthorizationCredentials = Depends(_bearer)):
    try:
        payload = jwt.decode(credentials.credentials, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    user = await User.find_one(User.user_id == user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    updates = body.model_dump(exclude_none=True)
    if updates:
        updates["update_time"] = datetime.now(timezone.utc)
        await user.update({"$set": updates})
        await user.sync()

    return MeResponse(
        user_id=user.user_id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        bio=user.bio,
        image_address=user.image_address,
        create_time=user.create_time,
        update_time=user.update_time,
    )
