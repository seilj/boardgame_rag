# 보드게임 규칙서 RAG 챗봇 프로젝트

### 세팅
1. poetry install 실행
2. .env.example파일을 .env파일로 바꾸고 변수 수정
3. services/db_manager.py 파일 실행

### 실행방법
루트디렉토리에서 아래 명령어 실행
- 개발용
```
uvicorn app:app --port 8501 --reload
```
- 배포용
```
uvicorn app:app --port 8501 --host 0.0.0.0 --timeout-keep-alive 30 
```

### 예시이미지

![image](https://github.com/user-attachments/assets/1954761d-f268-4162-a099-a5ec938b9dd4)
