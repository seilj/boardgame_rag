from fastapi import APIRouter, Depends
from app.database import db
from app.models import BoardGameSchema

router = APIRouter()

@router.post("/")
async def add_game(game: BoardGameSchema):
    result = await db.games.insert_one(game.dict())
    return {"inserted_id": str(result.inserted_id)}

@router.get("/{game_id}")
async def get_game(game_id: int):
    game = await db.games.find_one({"id": game_id})
    if game:
        game["_id"] = str(game["_id"])
        return game
    return {"error": "Game not found"}
