from typing import List
from pydantic import BaseModel

class BoardGameSchema(BaseModel):
    id: int
    name: str
    description: str
    min_players: int
    max_players: int
    recommended_players: List[int]
    rating: float
    mechanics: List[str]
    categories: List[str]
    min_age: int
    playtime: int
