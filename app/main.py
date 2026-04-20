from fastapi import FastAPI
from app.routers import auth

app = FastAPI(title="IP Group Assignment API")

app.include_router(auth.router)
