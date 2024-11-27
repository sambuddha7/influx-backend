from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from utils.reddit import search_subreddits, rank_subreddits

router = APIRouter()

# Define request schema
class KeywordRequest(BaseModel):
    keywords: List[str]

@router.post("/rank_subreddits/")
async def get_ranked_subreddits(data: KeywordRequest):
    try:
        # Search and rank subreddits
        subreddits = search_subreddits(data.keywords, limit=50)
        ranked_subreddits = rank_subreddits(subreddits)
        return {"subreddits": ranked_subreddits}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
