import os
import csv
import requests
import xml.etree.ElementTree as ET
import asyncio  # 비동기 함수 실행을 위해 asyncio 임포트
import json  # JSON 파일 저장을 위해 json 임포트
from app.services.bgg_service import fetch_bgg_thing

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # 현재 파일 위치
FILE_URL = os.path.join(BASE_DIR, "./gamelist_copy.csv")  # 절대 경로 변환
OUTPUT_FILE = os.path.join(BASE_DIR, "output.json")  # 출력할 파일 경로

# BGG API에서 보드게임 이름으로 ID를 받아오는 함수
def fetch_game_id_by_name(game_name: str):
    """게임 이름으로 BGG API에서 ID를 가져오는 함수"""
    try:
        url = f"https://www.boardgamegeek.com/xmlapi/search?search={game_name}"
        # SSL 인증서 검증 비활성화 (보안상 주의)
        response = requests.get(url, verify=True)
        response.raise_for_status()
        
        # BGG에서 받은 XML 데이터 파싱
        data = response.text
        
        # XML 파싱
        root = ET.fromstring(data)
        
        # 'boardgame' 태그에서 'objectid' 속성 값 추출
        boardgame = root.find('boardgame')
        if boardgame is not None:
            game_id = boardgame.get('objectid')
            return game_id
        else:
            return None  # 게임을 찾을 수 없음
    except requests.RequestException as e:
        print(f"Error fetching game ID for {game_name}: {e}")
        return None

# CSV에서 3번째 열을 추출하는 함수
def extract_third_column(file_path):
    """CSV 파일에서 3번째 열의 데이터를 리스트로 추출 (빈 칸은 제외)"""
    third_column_data = []
    
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        
        for row in reader:
            # 3번째 열이 존재하고, 값이 비어있지 않다면 추가
            if len(row) >= 3 and row[2].strip():
                third_column_data.append(row[2].strip())

    return third_column_data

# CSV 파일에서 게임 이름을 추출하고 ID를 받아오는 메인 함수
async def main():
    """CSV에서 보드게임 이름을 추출하고, 해당 이름으로 BGG ID를 가져오는 작업"""
    # 파일 경로 확인
    if not os.path.exists(FILE_URL):
        print(f"파일을 찾을 수 없습니다: {FILE_URL}")
        return

    # CSV에서 보드게임 이름을 추출
    game_names = extract_third_column(FILE_URL)

    # 보드게임 이름을 이용해 ID를 가져오는 작업
    game_ids = []
    for game_name in game_names:
        game_id = fetch_game_id_by_name(game_name)
        if game_id:
            game_ids.append(game_id)

    if game_ids:
        print("게임 ID 목록:")
        print(game_ids)
        
        # 게임 정보를 저장할 리스트
        game_data = []  # 리스트로 결과 저장

        # 게임 ID를 기반으로 BGG 정보를 가져오기
        for game_id in game_ids:
            game_info = await fetch_bgg_thing(game_id)  # 비동기적으로 BGG 정보 가져오기
            if game_info:
                game_data.append({"game_id": game_id, "game_info": game_info})

        # 게임 정보를 JSON 파일로 저장
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as output_file:
            json.dump(game_data, output_file, ensure_ascii=False, indent=4)  # JSON으로 저장

    else:
        print("게임 ID를 찾을 수 없습니다.")

# 스크립트 실행
if __name__ == "__main__":
    # async 메인 함수 실행을 위해 asyncio.run() 사용
    asyncio.run(main())
