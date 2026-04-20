from fastapi import APIRouter
from pydantic import BaseModel
from app.keys import public_key_pem

router = APIRouter(prefix="/auth", tags=["auth"])


class PublicKeyResponse(BaseModel):
    public_key: str


@router.get("/public-key", response_model=PublicKeyResponse)
def get_public_key():
    return PublicKeyResponse(public_key=public_key_pem)
