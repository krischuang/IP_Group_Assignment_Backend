from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.routers import auth
from app.database import connect_db, close_db
from app.models.user import User
from app.models.counter import Counter
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db(document_models=[User, Counter])
    yield
    await close_db()


app = FastAPI(title="IP Group Assignment API", lifespan=lifespan, root_path=settings.root_path)

app.include_router(auth.router)