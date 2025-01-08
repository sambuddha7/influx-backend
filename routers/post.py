from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
import pandas as pd
from utils.posts import find_relevant_posts, split_csv_string
from utils.firestore_service import FirestoreService

firestore_service = FirestoreService()
router = APIRouter()

class KeywordsInput(BaseModel):
    primary_keywords: List[str]
    secondary_keywords: List[str]
    limit: Optional[int] = 10000
    min_similarity: Optional[float] = 0.2

@router.get("/relevant_posts")
async def get_relevant_posts(userid):
    # Get keywords from Firestore
    # print(userid)
    keywords = await firestore_service.get_keywords(user_id=userid)
    keywords = split_csv_string(keywords)
    print(keywords)
    keywords = KeywordsInput(
        primary_keywords=keywords[0],
        secondary_keywords=keywords[1],
    )
    #reply_list = []
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
        for i in range(1, 4):
            print(results[i])
            print("\n#########")

        # id
        # subreddit
        # title
        # body
    #     reply_list = []
        iter = 0
        reply_list = []
        if len(results) < 10:
            iter = len(results)
        else:
            iter = 10
        for i in range(iter):
            obj = results[i] #victim of the crime
            llm_reply = "This is a placeholder reply"
            reddit_object = [obj["id"], obj["subreddit"], obj["title"], obj["body"], llm_reply]
            reply_list.append(reddit_object)

        return reply_list
        #return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error occurred: {str(e)}")