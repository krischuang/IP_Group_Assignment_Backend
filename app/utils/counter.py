from pymongo import ReturnDocument
from app.models.counter import Counter


async def _next_id(name: str) -> int:
    collection = Counter.get_motor_collection()
    result = await collection.find_one_and_update(
        {"name": name},
        {"$inc": {"value": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    return result["value"]
