from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from utils.finder import get_rising_posts, get_hot_posts, get_reply
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

reddit = praw.Reddit(
    client_id=os.getenv("CLIENT_ID1"),
    client_secret=os.getenv("CLIENT_SECRET1"),
    user_agent=os.getenv("USER_AGENT"),
    redirect_uri='http://localhost:8000/reddit_callback',
    username=os.getenv("USER_NAME"),
    password=os.getenv("PASSWORD"),
)

tracker = MetricsTracker(reddit)
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
def reply_to_reddit_post(request: ReplyRequest):
    try:
        # Fetch the submission using the post ID
        submission = reddit.submission(id=request.post_id)
        # Add a reply to the post
        reply = submission.reply(request.reply_text)
        tracker.add_reply(reply.id)
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



@router.get("/metrics")
def get_metrics():
    """Get current metrics for all tracked replies"""
    return tracker.get_metrics()