from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

client: AsyncIOMotorClient = None


async def connect_db(document_models: list):
    global client
    client = AsyncIOMotorClient(settings.mongodb_uri)
    await init_beanie(
        database=client[settings.db_name],
        document_models=document_models,
    )


async def close_db():
    global client
    if client:
        client.close()
