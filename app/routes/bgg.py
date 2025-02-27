from fastapi import APIRouter
from app.services.bgg_service import fetch_bgg_thing

router = APIRouter()

@router.get("/game/{id}")
async def get_game_info(id: int):
    """BGG API에서 보드게임 정보를 가져오는 엔드포인트 (RESTful)"""
    return await fetch_bgg_thing(id)


