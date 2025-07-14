from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
import pandas as pd
from utils.posts import find_relevant_posts, split_csv_string, search_reddit_new
from utils.search_posts import search_reddit_stream
from utils.firestore_service import FirestoreService
from utils.finder import filter_best_subreddits, get_hot_posts, get_rising_posts
from utils.web_search import prepare_vector, batch_upsert
from utils.pinecone_client import index
import asyncpraw
import os 

# from utils.post_scoring import final_df

firestore_service = FirestoreService()
router = APIRouter()

@router.get("/relevant_posts")
async def get_relevant_posts(userid):
    reddit = asyncpraw.Reddit(
        client_id=os.getenv("CLIENT_ID"),
        client_secret=os.getenv("CLIENT_SECRET"),
        user_agent=os.getenv("USER_AGENT"),
    )
    # Get keywords from Firestore
    keywords = await firestore_service.get_keywords(user_id=userid)
    keywords = keywords.split(',')
    subreddits = await firestore_service.get_subreddits(user_id=userid)
    subreddits = subreddits.split(',')

    try:
        # Use the new search_reddit_stream function
        results = await search_reddit_stream(
            reddit=reddit,
            keywords=keywords,
            target_subreddits=subreddits,
            max_posts=1000
        )
        # ...existing logic for processing posts...
        iter = 0
        reply_list = []
        if len(results) < 20:
            iter = len(results)
        else:
            iter = len(results)
        for i in range(iter):
            obj = results[i]
            llm_reply = "Add your reply here"
            reddit_object = [obj["id"], obj["subreddit"], obj["title"], obj["body"], llm_reply, obj["url"], obj["created_utc"]]
            reply_list.append(reddit_object)
        print("reached")
        print(len(reply_list), "reply list length")

        # Add posts to Pinecone with user namespace
        vectors_to_upsert = []

        for post in reply_list:
            try:
                vector = prepare_vector(post)
                vectors_to_upsert.append(vector)
            except Exception as e:
                print(f"Failed to process post ID {post[0]}: {e}")
        
        print("reached")

        if vectors_to_upsert:
            batch_upsert(index, vectors_to_upsert, namespace=userid)
        else:
            print("❌ No vectors were uploaded due to earlier errors.")
        # return reply_list
        return []

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error occurred: {str(e)}")
    

@router.get("/get_subreddits")
async def get_subreddits(userid):
    posts = await firestore_service.get_user_posts(userid)  
    print(posts)
    subs = {post["subreddit"] for post in posts if "subreddit" in post} 
    
    company_description = await firestore_service.get_company_description(user_id=userid)
    subreddit= filter_best_subreddits(subs, company_description)
    return subreddit
    
async def cron_job_helper(userid):
    primary = await firestore_service.get_primary_keywords(user_id=userid)
    secondary = await firestore_service.get_secondary_keywords(user_id=userid)
    excluded_subs = await firestore_service.get_excluded_reddits(user_id=userid)
    reddit_posts = await firestore_service.get_user_posts(user_id=userid)
    if isinstance(primary, str):
        primary = primary.split(',')
    if isinstance(secondary, str):
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
            duration="day",
            excluded_subs=excluded_subs,
            reddit_posts=reddit_posts
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
        if len(results) < 5:
            iter = len(results)
        else:
            iter = 5
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
        
        
@router.get("/subreddit_posts")
async def get_relevant_sub_posts(subreddit):
    """Get posts for a subreddit"""
    try:
        # Find relevant posts
        results_df = get_rising_posts(subreddit)
        if results_df.empty:
            return []

        # Convert DataFrame to list of dictionaries for response
        results = results_df.astype(object).to_dict(orient="records")

        # id
        # subreddit
        # title
        # body
        #url
        # date created
        # reply_list = []
        iter = 0
        reply_list = []
        if len(results) < 5:
            iter = len(results)
        else:
            iter = 5
        for i in range(iter):
            obj = results[i] 
            llm_reply = "Add your reply here"
            reddit_object = [obj["id"], obj["subreddit"], obj["title"], obj["body"], llm_reply, obj["url"], obj["created_utc"]]
            reply_list.append(reddit_object)

        
        return reply_list
        #return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error occurred: {str(e)}")