import os
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie, Document

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = "boardgame_db"

class BoardGame(Document):
    game_id: str
    game_info: dict
    game_vector: list  # 768차원 벡터 저장

    class Settings:
        collection = "boardgames"

async def init_mongodb():
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]
    await init_beanie(database=db, document_models=[BoardGame])
