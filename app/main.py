from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.routers import auth
from app.database import connect_db, close_db
from app.models.user import User
from app.models.counter import Counter


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db(document_models=[User, Counter])
    yield
    await close_db()


app = FastAPI(title="IP Group Assignment API", lifespan=lifespan)

app.include_router(auth.router)