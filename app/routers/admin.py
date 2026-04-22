from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, EmailStr
from app.dependencies import require_admin
from app.models.user import User, UserRole

router = APIRouter(prefix="/admin", tags=["admin"])


# ---------- Schemas ----------

class UserSummary(BaseModel):
    user_id: int
    email: str
    full_name: str
    role: UserRole
    bio: str | None
    image_address: str | None
    create_time: datetime
    update_time: datetime


class UsersResponse(BaseModel):
    total: int
    users: list[UserSummary]


class StatsResponse(BaseModel):
    total_users: int


class UpdateUserRequest(BaseModel):
    full_name: str | None = None
    email: EmailStr | None = None
    role: UserRole | None = None
    bio: str | None = None
    image_address: str | None = None


# ---------- Helpers ----------

def _to_summary(user: User) -> UserSummary:
    return UserSummary(
        user_id=user.user_id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        bio=user.bio,
        image_address=user.image_address,
        create_time=user.create_time,
        update_time=user.update_time,
    )


# ---------- Endpoints ----------

@router.get("/stats", response_model=StatsResponse)
async def get_stats(_admin=Depends(require_admin)):
    total_users = await User.count()
    return StatsResponse(total_users=total_users)


@router.get("/users", response_model=UsersResponse)
async def list_users(
    search: str | None = Query(default=None, description="Search by name, email, or role"),
    _admin=Depends(require_admin),
):
    all_users = await User.find_all().to_list()

    if search:
        q = search.lower()
        all_users = [
            u for u in all_users
            if q in u.full_name.lower()
            or q in u.email.lower()
            or q in u.role.lower()
        ]

    return UsersResponse(total=len(all_users), users=[_to_summary(u) for u in all_users])


@router.put("/users/{user_id}", response_model=UserSummary)
async def update_user(
    user_id: int,
    body: UpdateUserRequest,
    _admin=Depends(require_admin),
):
    user = await User.find_one(User.user_id == user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if body.email and body.email != user.email:
        conflict = await User.find_one(User.email == body.email)
        if conflict:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already in use")

    updates = body.model_dump(exclude_none=True)
    if updates:
        updates["update_time"] = datetime.now(timezone.utc)
        await user.update({"$set": updates})
        await user.sync()

    return _to_summary(user)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, admin=Depends(require_admin)):
    if admin.user_id == user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete your own account")

    user = await User.find_one(User.user_id == user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    await user.delete()
