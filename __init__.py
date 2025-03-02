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

# Pinecone API Key 및 환경 설정
load_dotenv()  # .env 파일을 로드
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_URL = os.path.join(BASE_DIR, "./data/gamelist.csv")
OUTPUT_FILE = os.path.join(BASE_DIR, "./data/output.json")

MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "boardgame_db"
openai.api_key = os.getenv("OPENAI_API_KEY")
print(openai.api_key)
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


def format_game_text(game_info):
    """보드게임 정보를 한 줄의 텍스트로 변환 (이름 제외)"""
    categories = ", ".join(game_info.get("link", {}).get("boardgamecategory", [])) or "N/A"
    mechanics = ", ".join(game_info.get("link", {}).get("boardgamemechanic", [])) or "N/A"
    players = f"{game_info.get('minplayers', 'N/A')} to {game_info.get('maxplayers', 'N/A')} players"
    playtime = f"{game_info.get('playingtime', 'N/A')} minutes"
    weight = f"Weight: {game_info.get('weight', 'N/A')}"
    rating = f"Rating: {game_info.get('ratings', 'N/A')}"

    # suggested_numplayers 데이터 추가
    suggested = game_info.get("suggested_numplayers", {})
    bestwith = ", ".join(map(str, suggested.get("bestwith", []))) or "N/A"
    recommendedwith = ", ".join(map(str, suggested.get("recommendedwith", []))) or "N/A"
    suggested_text = f"Best with {bestwith}. Recommended with {recommendedwith}."

    return f"Category: {categories}. Mechanic: {mechanics}. Players: {players}. Playtime: {playtime}. {weight}. {rating}. {suggested_text}"



def get_embedding(text):
    """텍스트를 OpenAI의 text-embedding-3-large 모델로 벡터화"""
    response = openai.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )
    
    # CreateEmbeddingResponse에서 data를 추출하고, 그 후 embedding을 가져오기
    embedding = response.data[0].embedding
    return embedding



# CSV -> BGG -> JSON 변환 + MongoDB 저장
async def main():
    if not os.path.exists(FILE_URL):
        print(f"파일을 찾을 수 없습니다: {FILE_URL}")
        return

    game_names = extract_third_column(FILE_URL)
    game_data = []
    pinecone_text_data = []
    pinecone_vector_data = []
    pinecone_name_data = []
    create_index()
    for game_name in game_names:
        game_id = fetch_game_id_by_name(game_name)
        print(f'게임 이름: {game_name}, 게임 ID: {game_id}')
        if game_id:
            game_info = await fetch_bgg_thing(game_id)
            if game_info:
                game_data.append({"game_id": game_id, "game_info": game_info})
                game_text = format_game_text(game_info)
                # 보드게임 정보 벡터화
                game_embedding = get_embedding(game_text)
                print(len(game_embedding))  # 출력: 768 (벡터 차원)
                print(game_embedding[:5])  # 벡터의 일부 출력
                game_text_data = {
                    "id": game_id,  # 여기서 game_id를 id로 사용
                    "text": game_text  # 보드게임의 텍스트 정보를 포함
                }
                pinecone_text_data.append(game_text_data)
                pinecone_vector_data.append(game_embedding)
                pinecone_name_data.append(game_name)
    upsert_vector(pinecone_text_data, pinecone_vector_data, pinecone_name_data)

    if game_data:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as output_file:
            json.dump(game_data, output_file, ensure_ascii=False, indent=4)
        print("게임 정보를 JSON 파일로 저장 완료!")

        #await insert_initial_data()  # MongoDB에 삽입

# 실행
if __name__ == "__main__":
    asyncio.run(main())
