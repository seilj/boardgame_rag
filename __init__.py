import os
import csv
import requests
import xml.etree.ElementTree as ET
import asyncio
import json
from motor.motor_asyncio import AsyncIOMotorClient  # MongoDB 비동기 클라이언트
from beanie import init_beanie, Document
from app.services.bgg_service import fetch_bgg_thing

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_URL = os.path.join(BASE_DIR, "./gamelist_copy.csv")
OUTPUT_FILE = os.path.join(BASE_DIR, "output.json")

MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "boardgame_db"

# Beanie 모델 정의
class BoardGame(Document):
    game_id: str
    game_info: dict

    class Settings:
        collection = "boardgames"  # MongoDB 컬렉션명

# MongoDB 연결 및 Beanie 초기화
async def init_db():
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]
    await init_beanie(database=db, document_models=[BoardGame])

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

# CSV에서 3번째 열 추출
def extract_third_column(file_path):
    third_column_data = []
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if len(row) >= 3 and row[2].strip():
                third_column_data.append(row[2].strip())
    return third_column_data

# JSON 데이터를 MongoDB에 삽입
async def insert_initial_data():
    await init_db()
    if not os.path.exists(OUTPUT_FILE):
        print("JSON 파일이 존재하지 않습니다.")
        return

    with open(OUTPUT_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)

    await BoardGame.find_all().delete()  # 기존 데이터 삭제
    game_entries = [BoardGame(game_id=game["game_id"], game_info=game["game_info"]) for game in data]
    await BoardGame.insert_many(game_entries)
    print("초기 데이터를 MongoDB에 삽입 완료!")

# CSV -> BGG -> JSON 변환 + MongoDB 저장
async def main():
    if not os.path.exists(FILE_URL):
        print(f"파일을 찾을 수 없습니다: {FILE_URL}")
        return

    game_names = extract_third_column(FILE_URL)
    game_data = []

    for game_name in game_names:
        game_id = fetch_game_id_by_name(game_name)
        if game_id:
            game_info = await fetch_bgg_thing(game_id)
            if game_info:
                game_data.append({"game_id": game_id, "game_info": game_info})

    if game_data:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as output_file:
            json.dump(game_data, output_file, ensure_ascii=False, indent=4)
        print("게임 정보를 JSON 파일로 저장 완료!")

        await insert_initial_data()  # MongoDB에 삽입

# 실행
if __name__ == "__main__":
    asyncio.run(main())
