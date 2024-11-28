import praw
from datetime import datetime
import os
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

reddit = praw.Reddit(
    client_id=os.getenv("CLIENT_ID"),
    client_secret=os.getenv("CLIENT_SECRET"),
    user_agent=os.getenv("USER_AGENT"),
)


def get_submission_data(subreddit_name, limit=500):
    subreddit = reddit.subreddit(subreddit_name)
    data = []
    for submission in subreddit.new(limit=limit):  
        data.append({
            "title": submission.title,
            "created_utc": submission.created_utc,
            "score": submission.score,
            "num_comments": submission.num_comments
        })
    return data


def analyze_posting_times(data):
    df = pd.DataFrame(data)
    df['created_at'] = pd.to_datetime(df['created_utc'], unit='s')
    df['hour'] = df['created_at'].dt.hour
    df['day_of_week'] = df['created_at'].dt.day_name()
    grouped = df.groupby(['day_of_week', 'hour']).agg({
        'score': 'mean',
        'num_comments': 'mean'
    }).reset_index()
    
    grouped['engagement_score'] = (
            (df['score'] * 0.5) + 
            (df['num_comments'] * 0.5)
        )
    
    return grouped.sort_values('engagement_score', ascending=False)


def plot_engagement_heatmap(grouped_data):
    pivot_table = grouped_data.pivot("day_of_week", "hour", "engagement_score")
    plt.figure(figsize=(12, 6))
    sns.heatmap(pivot_table, cmap="coolwarm", annot=True, fmt=".1f")
    plt.title("Engagement Heatmap")
    plt.show()
    

#main function to call for finding best time
def get_best_posting_times(subreddits):
    results = {}
    for subreddit in subreddits:
        data = get_submission_data(subreddit)
        grouped_data = analyze_posting_times(data)
        best_times = grouped_data.head(5)  
        results[subreddit] = best_times
    return results