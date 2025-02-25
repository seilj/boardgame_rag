from fastapi import APIRouter
from app.services.bgg_service import fetch_bgg_game, fetch_bgg_game_raw

router = APIRouter()

@router.get("/game/{id}")
async def get_game_info(id: int):
    """BGG API에서 보드게임 정보를 가져오는 엔드포인트 (RESTful)"""
    return await fetch_bgg_game(id)

@router.get("/game/{id}/raw")
async def get_game_raw(id: int):
    """BGG API에서 원본 XML 데이터를 가져오는 엔드포인트"""
    return {"id": id, "raw_xml": await fetch_bgg_game_raw(id)}
