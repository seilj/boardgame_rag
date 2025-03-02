import openai
from ..db.pinecone_db import save_to_pinecone

def format_game_text(game_info):
    """보드게임 정보를 텍스트로 변환"""
    categories = ", ".join(game_info["link"]["boardgamecategory"])
    mechanics = ", ".join(game_info["link"]["boardgamemechanic"])
    players = f"{game_info['minplayers']} to {game_info['maxplayers']} players"
    playtime = f"{game_info['playingtime']} minutes"
    weight = f"Weight: {game_info['weight']}"
    rating = f"Rating: {game_info['ratings']}"

    return f"Category: {categories}. Mechanic: {mechanics}. Players: {players}. Playtime: {playtime}. {weight}. {rating}."

def get_embedding(text):
    """텍스트를 OpenAI 임베딩으로 변환"""
    response = openai.embeddings.create(
        input=text,
        model="text-embedding-3-large"
    )
    return response["data"][0]["embedding"]

def process_and_store_embedding(game_id, game_info):
    """보드게임 정보를 벡터화하고 Pinecone에 저장"""
    text = format_game_text(game_info)
    embedding = get_embedding(text)
    
    metadata = {
        "name": game_info["name"],
        "category": game_info["link"]["boardgamecategory"],
        "mechanic": game_info["link"]["boardgamemechanic"]
    }
    
    save_to_pinecone(game_id, embedding, metadata)
    return embedding
