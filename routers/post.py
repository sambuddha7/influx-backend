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
    min_similarity: Optional[float] = 0.1

@router.get("/relevant_posts")
async def get_relevant_posts(userid):
    # Get keywords from Firestore
    # keywords = await firestore_service.get_keywords(user_id=userid)
    # keywords = split_csv_string(keywords)
    primary = await firestore_service.get_primary_keywords(user_id=userid)
    secondary = await firestore_service.get_secondary_keywords(user_id=userid)
    primary = primary.split(',')
    secondary = secondary.split(',')
    keywords = KeywordsInput(
        primary_keywords=primary,
        secondary_keywords=secondary,
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

        # id
        # subreddit
        # title
        # body
    #     reply_list = []
        iter = 0
        reply_list = []
        if len(results) < 20:
            iter = len(results)
        else:
            iter = 20
        for i in range(iter):
            obj = results[i] #victim of the crime
            llm_reply = "Add your reply here"
            reddit_object = [obj["id"], obj["subreddit"], obj["title"], obj["body"], llm_reply, obj["url"], obj["created_utc"]]
            reply_list.append(reddit_object)

        return reply_list
        #return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error occurred: {str(e)}")
    
async def cron_job_helper(userid):
    primary = await firestore_service.get_primary_keywords(user_id=userid)
    secondary = await firestore_service.get_secondary_keywords(user_id=userid)
    primary = primary.split(',')
    secondary = secondary.split(',')
    keywords = KeywordsInput(
        primary_keywords=primary,
        secondary_keywords=secondary,
    )
    try:
        # Find relevant posts
        results_df = find_relevant_posts(
            primary_keywords=keywords.primary_keywords,
            secondary_keywords=keywords.secondary_keywords,
            limit=keywords.limit,
            min_similarity=keywords.min_similarity,
            duration="day"
        )

        if results_df.empty:
            return []

        # Convert DataFrame to list of dictionaries for response
        results = results_df.astype(object).to_dict(orient="records")

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
            llm_reply = "Add your reply here"
            # reddit_object = [obj["id"], obj["subreddit"], obj["title"], obj["body"], llm_reply]

            reddit_object = [obj["id"], obj["subreddit"], obj["title"], obj["body"], llm_reply, obj["url"], obj["created_utc"]]

            reply_list.append(reddit_object)
            await firestore_service.add_post(userid, reddit_object)

        return reply_list
        #return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error occurred: {str(e)}")

# @router.get("/relevant_posts_weekly")
async def get_relevant_posts_weekly_job():
    # Get keywords from Firestore
    print("cron jobbb")
    active_users = await firestore_service.get_active_user_ids()
    for user in active_users:
        await cron_job_helper(user)