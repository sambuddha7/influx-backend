from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from utils.finder import get_reply, get_keywords, get_reply_comm, get_reply_feedback, get_description, get_subreddits, get_phrases
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

@router.post("/regenerate-reply")
async def get_reps_feedback(request: dict):
    post_data = request.get("post")
    feedback = request.get("feedback")
    
    print(f"Feedback: {feedback}")
    
    # Extract post context
    post_title = post_data.get("title", "")
    post_content = post_data.get("content", "")
    subreddit = post_data.get("subreddit", "")
    current_reply = post_data.get("suggested_reply", "")
    
    # Pass all context to the function
    llm_reply = get_reply_feedback(
        initial_reply=current_reply,
        feedback=feedback,
        post_title=post_title,
        post_content=post_content,
        subreddit=subreddit
    )
    
    print(f"Generated reply: {llm_reply}")
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
        print(f"generated keywords: {keywords}")
        return keywords
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/paraphrases")
async def get_paraphrases_from_description(description: str):
    try:
        phrases = get_phrases(description)
        print(f"generated phrases: {phrases}")
        return phrases
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/generate_subreddits")
async def get_subreddits_from_description(description: str):
    try:
        subreddits = get_subreddits(description)
        print(f"generated subreddits: {subreddits}")
        return subreddits
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



class ContentInput(BaseModel):
    content: str
    companyName: str

@router.post("/company_desc")
async def get_company_description(input: ContentInput):
    final_str="company name:" + input.companyName + "\n" +input.content
    print(final_str)
    try:
        desc = get_description(final_str)
        desc = desc.strip('"')
        return desc
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))