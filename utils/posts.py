import praw
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple
from datetime import datetime
import os 
from dotenv import load_dotenv

load_dotenv()

reddit = praw.Reddit(
    client_id=os.getenv("CLIENT_ID"),
    client_secret=os.getenv("CLIENT_SECRET"),
    user_agent=os.getenv("USER_AGENT"),
)

vectorizer = TfidfVectorizer(
    stop_words='english',
    max_features=5000,
    ngram_range=(1, 3),
    analyzer='word',
    token_pattern=r'(?u)\b\w+\b'
)

def fetch_reddit_posts(search_query: str, limit: int) -> List[Dict]:
    """
    Fetch posts from all of Reddit based on search query
    
    Args:
        search_query (str): Search query string
        limit (int): Maximum number of posts to fetch
        
    Returns:
        List[Dict]: List of posts with their details
    """
    posts = []
    
    for submission in reddit.subreddit("all").search(
        search_query, 
        sort='relevance', 
        time_filter='month',
        limit=limit
    ):
        posts.append({
            'id': submission.id,
            'title': submission.title,
            'body': submission.selftext,
            'url': f"https://reddit.com{submission.permalink}",
            'score': submission.score,
            'created_utc': datetime.fromtimestamp(submission.created_utc),
            'num_comments': submission.num_comments,
            'subreddit': submission.subreddit.display_name
        })
    
    return posts

def calculate_keyword_scores(text: str, 
                           primary_keywords: List[str], 
                           secondary_keywords: List[str]) -> Tuple[float, float]:
    """
    Calculate separate scores for primary and secondary keyword matches
    
    Args:
        text (str): Text to analyze
        primary_keywords (List[str]): List of primary keywords
        secondary_keywords (List[str]): List of secondary keywords
        
    Returns:
        Tuple[float, float]: Primary and secondary keyword scores
    """
    text_lower = text.lower()
    
    # Calculate primary keyword matches
    primary_matches = sum(1 for kw in primary_keywords 
                         if kw.lower() in text_lower)
    primary_score = primary_matches / len(primary_keywords)
    
    # Calculate secondary keyword matches
    secondary_matches = sum(1 for kw in secondary_keywords 
                          if kw.lower() in text_lower)
    secondary_score = secondary_matches / len(secondary_keywords) if secondary_keywords else 0
    
    return primary_score, secondary_score

def find_relevant_posts(primary_keywords: List[str],
                       secondary_keywords: List[str],
                       limit: int,
                       min_similarity: float = 0.1,
                       primary_weight: float = 0.7,
                       secondary_weight: float = 0.3) -> pd.DataFrame:
    """
    Find posts relevant to given primary and secondary keywords
    
    Args:
        primary_keywords (List[str]): List of primary keywords (must match)
        secondary_keywords (List[str]): List of secondary/context keywords
        limit (int): Maximum posts to fetch
        min_similarity (float): Minimum combined similarity score
        primary_weight (float): Weight for primary keyword similarity (0-1)
        secondary_weight (float): Weight for secondary keyword similarity (0-1)
        
    Returns:
        pd.DataFrame: Sorted dataframe of relevant posts
    """
    # Create search query from primary keywords
    search_query = ' OR '.join(f'"{kw}"' for kw in primary_keywords)
    
    # Fetch posts using Reddit's search
    all_posts = fetch_reddit_posts(search_query, limit=limit)
    
    if not all_posts:
        return pd.DataFrame()
    
    # Combine title and body for text analysis
    posts_text = [f"{post['title']} {post['body']}" for post in all_posts]
    
    # Calculate TF-IDF similarity scores
    primary_query = ' '.join(primary_keywords)
    secondary_query = ' '.join(secondary_keywords)
    
    # Vectorize posts and both keyword queries
    tfidf_matrix = vectorizer.fit_transform(
        posts_text + [primary_query, secondary_query]
    )
    
    # Calculate similarity scores for both keyword sets
    primary_similarities = cosine_similarity(
        tfidf_matrix[-2:-1], 
        tfidf_matrix[:-2]
    )[0]
    
    secondary_similarities = cosine_similarity(
        tfidf_matrix[-1:], 
        tfidf_matrix[:-2]
    )[0]
    
    # Calculate keyword presence scores
    keyword_scores = [
        calculate_keyword_scores(text, primary_keywords, secondary_keywords)
        for text in posts_text
    ]
    
    primary_keyword_scores = np.array([score[0] for score in keyword_scores])
    secondary_keyword_scores = np.array([score[1] for score in keyword_scores])
    
    # Combine TF-IDF and keyword presence scores
    combined_primary_scores = (primary_similarities + primary_keyword_scores) / 2
    combined_secondary_scores = (secondary_similarities + secondary_keyword_scores) / 2
    
    # Calculate final weighted scores
    final_scores = (
        primary_weight * combined_primary_scores + 
        secondary_weight * combined_secondary_scores
    )
    
    # Create DataFrame with results
    results_df = pd.DataFrame(all_posts)
    results_df['similarity_score'] = final_scores
    results_df['primary_score'] = combined_primary_scores
    results_df['secondary_score'] = combined_secondary_scores
    
    # Filter and sort results
    relevant_posts = results_df[results_df['similarity_score'] >= min_similarity]
    relevant_posts = relevant_posts.sort_values(
        by=['similarity_score', 'score'], 
        ascending=[False, False]
    )
    
    return relevant_posts