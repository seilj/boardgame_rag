# from fastapi import FastAPI, Depends, Request, HTTPException
# from fastapi.responses import HTMLResponse, StreamingResponse, RedirectResponse, JSONResponse
# from fastapi.staticfiles import StaticFiles
# from fastapi.middleware.cors import CORSMiddleware
# from typing import AsyncGenerator
# import asyncio
# import logging
# from services.retriever_manager import RetrieverManager
# from services.rag_chain import RAGChain
# from pymongo import MongoClient

# from dotenv import load_dotenv
# load_dotenv(override=True)

# app = FastAPI()
# app.mount("/static", StaticFiles(directory="static"), name="static")

# # CORS middleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://localhost:8501"],
# )

# # MONGO_URI = os.getenv("MONGO_URI")
# # client = MongoClient(MONGO_URI)

# # @app.route("/")
# # def index():
# #     with open("static/login.html", encoding="utf-8") as f:
# #         return HTMLResponse(content=f.read())

# @app.get("/")
# async def root():
#     return RedirectResponse(url="/chat")

# @app.get("/chat")
# async def get():
#     with open("static/chat.html", encoding="utf-8") as f:
#         return HTMLResponse(content=f.read())
    
# @app.get("/games")
# async def get_games(request: Request):
#     #TODO game list 어떻게 불러올건지 결정
#     referer = request.headers.get("Referer")
#     if not referer or not referer.endswith("/chat"):
#         raise HTTPException(status_code=403, detail="Forbidden")

#     # collection = client["db"]["boardgame"]
#     # games = collection.find({}, {"game_name": 1, "_id": 0})
#     # game_list = [game["game_name"] for game in games]
#     game_list = ["카탄", "윙스팬", "뤄양의 사람들", "아컴호러", "아그리콜라"]
#     return {"games": game_list}
    
# async def generate_response(query: dict) -> AsyncGenerator[str, None]:
#     retriever_manager = RetrieverManager(query["game_name"])
#     rag_chain = RAGChain(retriever_manager)
#     for chunk in rag_chain.stream(query):
#         yield chunk
#         await asyncio.sleep(0)  # Allow other tasks to run
    
# @app.post("/chat")
# async def chat(request: Request):
#     # ex) query = {
#     #     "question": "question about the game",
#     #     "game_name": "카탄",
#     #     "session_id": "unique session id"
#     # }
    
#     query = await request.json()
#     logging.info(f"query info: {query}")
    
#     return StreamingResponse(
#         generate_response(query),
#         media_type="text/event-stream"
#     )

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run("app:app", host="0.0.0.0", port=8501, reload=True)

from fastapi import FastAPI
from app.routes import bgg, games,data

app = FastAPI(title="Boardgame API")

# 라우터 등록
app.include_router(bgg.router, prefix="/bgg", tags=["BoardGameGeek"])
app.include_router(games.router, prefix="/games", tags=["Games"])
app.include_router(data.router, prefix="/data", tags=["Data"])

@app.get("/")
def home():
    return {"message": "Welcome to Boardgame API!"}
