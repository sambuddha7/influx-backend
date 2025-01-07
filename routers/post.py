from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
import pandas as pd
from utils.posts import find_relevant_posts

router = APIRouter()

class KeywordsInput(BaseModel):
    primary_keywords: List[str]
    secondary_keywords: List[str]
    limit: Optional[int] = 10000
    min_similarity: Optional[float] = 0.3

@router.get("/relevant_posts")
async def get_relevant_posts(keywords: KeywordsInput):
    try:
        # Find relevant posts
        results_df = find_relevant_posts(
            primary_keywords=keywords.primary_keywords,
            secondary_keywords=keywords.secondary_keywords,
            limit=keywords.limit,
            min_similarity=keywords.min_similarity
        )

        if results_df.empty:
            return []

        # Convert DataFrame to list of dictionaries for response
        results = results_df.astype(object).to_dict(orient="records")
        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error occurred: {str(e)}")