from pinecone.grpc import PineconeGRPC as Pinecone
from pinecone_test import ServerlessSpec
import time
import os
# Pinecone 클라이언트 생성
from dotenv import load_dotenv

def save_to_pinecone(data, index_name):
    load_dotenv()  # .env 파일을 로드
    print(os.getenv("PINECONE_API_KEY"))
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"), environment="us-west1-gcp")

    # 인덱스 이름 설정
    index_name = "example-index"

    # 인덱스가 없다면 서버리스 인덱스를 생성
    if index_name not in pc.list_indexes():
        pc.create_index(
            name=index_name,
            dimension=1024,  # 벡터 차원 크기
            metric="cosine",  # 거리 측정 방법
            spec=ServerlessSpec(
                cloud="aws",  # 사용할 클라우드 제공자
                region="us-east-1"  # 사용할 리전
            )
        )

    # 인덱스가 준비될 때까지 기다림
    while pc.describe_index(index_name).status['ready'] is False:
        print(f"{index_name} 인덱스가 준비되지 않았습니다. 기다리는 중...")
        time.sleep(1)  # 1초 대기

    print(f"{index_name} 인덱스가 준비되었습니다!")
