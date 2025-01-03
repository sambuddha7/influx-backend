from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from utils.finder import get_rising_posts, get_hot_posts, get_reply
from typing import List
from dotenv import load_dotenv
import praw
import os


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


@router.get("/posts")
def get_posts():
    subreddit = "CRM"
    hot_posts = get_hot_posts(subreddit)
    reply_list = []
    for i in hot_posts:
        # 0 -> id
        # 1 -> title
        # 2 -> content
        llm_reply = get_reply(f"title:{i[1]} content: {i[2]}")
        reddit_object = [i[0], subreddit, i[1], i[2], llm_reply]
        reply_list.append(reddit_object)
    return reply_list
