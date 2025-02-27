from fastapi import APIRouter
from app.services.data import extract_third_column
import os

router = APIRouter()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # 현재 파일 위치
FILE_URL = os.path.join(BASE_DIR, "../../gamelist.csv")  # 절대 경로 변환

@router.get("/data")
async def put_data_by_csv():
    """테스트용 데이터 파싱"""
    return extract_third_column(FILE_URL)