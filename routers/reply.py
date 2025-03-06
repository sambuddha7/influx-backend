from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from utils.finder import get_rising_posts, get_hot_posts, get_reply, get_keywords, get_reply_comm
from utils.tracker import MetricsTracker
from typing import List
from dotenv import load_dotenv
import praw
import os
from utils.firestore_service import FirestoreService

firestore_service = FirestoreService()
router = APIRouter()


load_dotenv()

router = APIRouter()
api_url = os.getenv("api_url")

reddit = praw.Reddit(
    client_id=os.getenv("CLIENT_ID2"),
    client_secret=os.getenv("CLIENT_SECRET2"),
    user_agent=os.getenv("USER_AGENT2"),
    redirect_uri=f"{api_url}/reddit_callback",
    username=os.getenv("USER_NAME2"),
    password=os.getenv("PASSWORD2"),
)

tracker = MetricsTracker(reddit, firestore_service)
class ReplyRequest(BaseModel):
    post_id: str = Field(..., min_length=1)
    reply_text: str = Field(..., min_length=1)
class RedditPost(BaseModel):
    id: str
    subreddit: str
    title: str
    content: str
    suggested_reply: str


@router.post("/reply_to_post")
async def reply_to_reddit_post(request: ReplyRequest, userid: str):
    try:
        # Fetch the submission using the post ID
        submission = reddit.submission(id=request.post_id)
        # Add a reply to the post
        reply = submission.reply(request.reply_text)
        await tracker.add_reply(userid, reply.id)
        return {
            "status": "success", 
            "message": "Reply submitted successfully",
            "reply_id": reply.id
        }
    except praw.exceptions.APIException as e:
        # Handle Reddit API specific errors
        raise HTTPException(status_code=400, detail=f"Reddit API Error: {str(e)}")
    except Exception as e:
        # Handle any other unexpected errors
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    
@router.post("/reply")
async def get_reps(post: RedditPost, userid):
    company_description = await firestore_service.get_company_description(user_id=userid) #1
    company_name = await firestore_service.get_company_name(user_id=userid) #2
    user_role = await firestore_service.get_user_role(user_id=userid) #3
    sample_reply =  await firestore_service.get_sample_reply(user_id=userid)#4 
    marketing_goals = await firestore_service.get_marketing_objectives(user_id=userid) #5
    llm_reply = get_reply(f"title:{post.title} content: {post.content}", company_name, company_description, user_role, sample_reply, marketing_goals) # llm call 
    return llm_reply

@router.post("/community_reply")
async def get_comm_reps(post: RedditPost, userid):
    company_description = await firestore_service.get_company_description(user_id=userid) #1
    company_name = await firestore_service.get_company_name(user_id=userid) #2
    user_role = await firestore_service.get_user_role(user_id=userid) #3
    sample_reply =  await firestore_service.get_sample_reply(user_id=userid)#4 
    marketing_goals = await firestore_service.get_marketing_objectives(user_id=userid) #5
    llm_reply = get_reply_comm(f"title:{post.title} content: {post.content}", company_name, company_description, user_role, sample_reply, marketing_goals) # llm call 
    return llm_reply
@router.post("/keywords")
async def get_keywords_from_description(description: str):
    try:
        keywords = get_keywords(description)
        return keywords
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics")
async def get_metrics(userid: str):
    """Get current metrics for all tracked replies"""
    metrics = await tracker.get_metrics(userid)
    return metrics