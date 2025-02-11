from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import AsyncGenerator
import asyncio
import logging
from services.retriever_manager import RetrieverManager
from services.rag_chain import RAGChain

from dotenv import load_dotenv
load_dotenv(override=True)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return RedirectResponse(url="/chat")

@app.get("/chat")
async def get():
    with open("static/chat.html", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())
    
async def generate_response(query: dict) -> AsyncGenerator[str, None]:
    retriever_manager = RetrieverManager(query["game_name"])
    rag_chain = RAGChain(retriever_manager)
    for chunk in rag_chain.stream(query):
        yield chunk
        await asyncio.sleep(0)  # Allow other tasks to run
    
@app.post("/chat")
async def chat(request: Request):
    # ex) query = {
    #     "question": "question about the game",
    #     "game_name": "카탄",
    #     "session_id": "unique session id"
    # }
    query = await request.json()
    logging.info(f"query info: {query}")
    
    return StreamingResponse(
        generate_response(query),
        media_type="text/event-stream"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8501, reload=True)