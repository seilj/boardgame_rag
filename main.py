import os
import csv
import requests
import xml.etree.ElementTree as ET
import asyncio
import json
from motor.motor_asyncio import AsyncIOMotorClient  # MongoDB 비동기 클라이언트
from beanie import init_beanie, Document
from app.services.bgg_service import fetch_bgg_thing
import openai
from dotenv import load_dotenv
from pinecone_test import create_index, upsert_vector

# BGG API에서 보드게임 ID 가져오기
def fetch_game_id_by_name(game_name: str):
    try:
        url = f"https://www.boardgamegeek.com/xmlapi/search?search={game_name}"
        response = requests.get(url, verify=True)
        response.raise_for_status()
        
        root = ET.fromstring(response.text)
        boardgame = root.find('boardgame')
        return boardgame.get('objectid') if boardgame is not None else None
    except requests.RequestException as e:
        print(f"Error fetching game ID for {game_name}: {e}")
        return None

async def main():
    print(fetch_game_id_by_name("타기론"))
    print(fetch_game_id_by_name("황혼의투쟁"))
    print(await fetch_bgg_thing(227466))
    print(await fetch_bgg_thing(12333))

if __name__ == "__main__":
    asyncio.run(main())
