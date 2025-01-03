import praw
import re
from dotenv import load_dotenv
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from itertools import chain
# from openai import OpenAI

# Load environment variables
load_dotenv()

# client = OpenAI()

# Initialize Reddit API
reddit = praw.Reddit(
    client_id=os.getenv("CLIENT_ID"),
    client_secret=os.getenv("CLIENT_SECRET"),
    user_agent=os.getenv("USER_AGENT"),
)

# Helper functions

# def generate_keywords(content) :
#     completion = client.chat.completions.create(
#         model="gpt-3.5-turbo-0125",
#         messages=[
#             {"role": "system", "content": "You are a helpful assistant."},
#             {
#                 "role": "user",
#                 "content": (
#                     "Extract a list of keywords from the following content. "
#                     "Return the keywords as a Python list of strings. "
#                     "Ensure the output is valid Python syntax.\n\n"
#                     f"Content: {content}"
#                 )
#             }
#         ]
#     )
#     print(completion.choices[0].message['content'])
#     return completion.choices[0].message['content']



def calculate_relevancy(subreddit, keywords):
    keyword_pattern = r'\b(?:' + '|'.join(re.escape(keyword.lower()) for keyword in keywords) + r')\b'
    title = subreddit.title.lower()
    description = subreddit.public_description.lower()
    title_matches = len(set(re.findall(keyword_pattern, title)))
    description_matches = len(set(re.findall(keyword_pattern, description)))
    score = (2 * title_matches) + description_matches
    return score

def search_subreddits(keywords, limit):
    subreddits = {}
    for keyword in keywords:
        for subreddit in reddit.subreddits.search(keyword, limit=limit):
            relevancy_score = calculate_relevancy(subreddit, keywords)
            if (subreddit.subscribers is not None) and subreddit.subscribers > 10000 and relevancy_score > 0: 
                subreddits[subreddit.display_name] = {
                    "name": subreddit.display_name,
                    "title": subreddit.title,
                    "description": subreddit.public_description,
                    "subscribers": subreddit.subscribers,
                    "active_users": subreddit.active_user_count,
                    "relevance": relevancy_score
                }
    return subreddits

def fetch_engagement(subreddit_name):
    subreddit = reddit.subreddit(subreddit_name)
    posts = chain(subreddit.hot(limit=10), subreddit.new(limit=10))
    total_comments = 0
    total_upvotes = 0
    post_count = 0

    for post in posts:
        total_comments += post.num_comments
        total_upvotes += post.score
        post_count += 1
    
    if post_count == 0: 
        return {"avg_comments": 0, "avg_upvotes": 0}

    return {
        "avg_comments": total_comments / post_count,
        "avg_upvotes": total_upvotes / post_count,
    }

def get_subreddit_activity_score(subreddit_name, lookback_days=90):
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=lookback_days)
    subreddit = reddit.subreddit(subreddit_name)
    total_posts = 0
    total_comments = 0
    recent_post_time = None
    recent_comment_time = None

    for submission in subreddit.new(limit=10):  
        post_time = datetime.utcfromtimestamp(submission.created_utc)
        if post_time >= start_time:
            total_posts += 1
            if not recent_post_time or post_time > recent_post_time:
                recent_post_time = post_time

    for comment in subreddit.comments(limit=1000):
        comment_time = datetime.utcfromtimestamp(comment.created_utc)
        if comment_time >= start_time:
            total_comments += 1
            if not recent_comment_time or comment_time > recent_comment_time:
                recent_comment_time = comment_time

    recency_score = 100 if (recent_comment_time and recent_post_time and recent_post_time >= start_time) else 0
    engagement_score = (total_posts + total_comments) / (subreddit.subscribers)
    activity_score = (total_posts * 0.4) + (total_comments * 0.4) + (engagement_score * 0.2) + recency_score

    return activity_score

def rank_subreddits(subreddits):
    ranked_list = []
    for name, data in subreddits.items():
        engagement = fetch_engagement(name)
        engagement_score = engagement["avg_comments"] + engagement["avg_upvotes"]
        size_score = data["subscribers"]
        activity_score = get_subreddit_activity_score(name)

        ranked_list.append({
            "subreddit": name,
            "engagement": engagement_score,
            "size": size_score,
            "activity": activity_score,
            "relevance": data.get("relevance", 0) 
        })

    df = pd.DataFrame(ranked_list)
    for col in ["engagement", "activity", "relevance"]:
        df[f"{col}_std"] = (df[col] - df[col].mean()) / df[col].std()

    weights = {"engagement_std": 0.3, "activity_std": 0.3, "relevance_std": 0.4}
    df["score"] = (
        weights["engagement_std"] * df["engagement_std"] +
        weights["activity_std"] * df["activity_std"] +
        weights["relevance_std"] * df["relevance_std"]
    )

    top_subreddits = df.sort_values("score", ascending=False).head(5)
    return top_subreddits.to_dict(orient="records")