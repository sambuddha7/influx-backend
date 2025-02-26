import praw
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple
from datetime import datetime
import os 
import re 
from dotenv import load_dotenv
from itertools import combinations
from datetime import datetime, timedelta


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
def split_csv_string(csv_string: str) -> list:
    # Split the CSV string into a list of words based on commas
    words = csv_string.split(",")
    
    # Get the first two words
    first_two_words = words[:2]
    
    # Get the rest of the words
    rest_of_words = words[2:]
    
    # Return the result as a 2D list
    return [first_two_words, rest_of_words]


def contains_url(post_body):
    """
    Check if a Reddit post body contains a URL.
    Returns True if URL is found, False otherwise.
    """
    # Common URL patterns
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    
    # Reddit markdown URL pattern [text](url)
    markdown_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    
    # Check for both raw URLs and markdown URLs
    has_raw_url = bool(re.search(url_pattern, post_body))
    has_markdown_url = bool(re.search(markdown_pattern, post_body))
    
    return has_raw_url or has_markdown_url


def is_promotional(submission) -> bool:

        title_lower = submission.title.lower()
        
        # Title prefix patterns
        prefix_patterns = [
            r'^\[(hiring|ad|advertisement|sponsored|promo|promotion|deal|sale|' \
            r'discount|giveaway|contest|affiliate|referral)\]',
            r'^\((hiring|ad|advertisement|sponsored|promo|promotion|deal|sale|' \
            r'discount|giveaway|contest|affiliate|referral)\)',
        ]
        body_lower = submission.selftext.lower()
        
        if(not body_lower) :
            return True
        
        if title_lower.startswith('[hiring]') or body_lower.startswith('[hiring]') or title_lower.startswith('hiring:'):
            return True
        
        # General promotional patterns
        promo_patterns = [
            r'\d+%\s*off',
            r'save\s*\$?\d+',
            r'limited\s*time\s*offer',
            r'click\s*here\s*to',
            r'dm\s*for\s*promo',
            r'discount\s*code',
            r'exclusive\s*offer',
            r'special\s*price',
            r'^now\s*available',
            r'buy\s*now',
            r'order\s*now',
            r'sale\s*ends',
        ]
        
        # Check title patterns
        if any(re.search(pattern, title_lower) for pattern in prefix_patterns + promo_patterns):
            return True
               
        # Check flair
        if submission.link_flair_text and any(term in str(submission.link_flair_text).lower() 
            for term in ['ad', 'sponsored', 'advertisement', 'promotion']):
            return True
        
        if "coupon code" in title_lower or "promo code" in title_lower or "hiring" in title_lower or "hiring" in body_lower or "hire" in title_lower:
            return True
        
        
        headers = [line for line in body_lower.split('\n') 
              if line.strip().startswith('#')]
        has_multiple_headers = len(headers) > 3
        

        bullets = [line for line in body_lower.split('\n') 
                if line.strip().startswith(('*', '-', '+'))]
        has_bullets = len(bullets) > 3
        
        promotional_keywords = [
            "pricing", "plans", "save", "free trial", 
            "special offer", "key features", "pros and cons", "try for free",
            "buy now", "coupon code"
        ]
        
        # Count occurrences of keywords in title and body
        keyword_count = sum(
            1 for keyword in promotional_keywords 
            if keyword in title_lower or keyword in body_lower
        )
    
            
        if contains_url(body_lower) and (len(body_lower.split()) > 300) and has_bullets and has_multiple_headers and submission.num_comments < 3 :
            return True
                               
        if not body_lower and submission.num_comments < 3 :
            return True  
        
        if len(body_lower) > 1000 : 
            return True
               
        return False

def fetch_reddit_posts(search_query: str, limit: int, duration, seen_posts) -> List[Dict]:
    """
    Fetch posts from all of Reddit based on search query
    
    Args:
        search_query (str): Search query string
        limit (int): Maximum number of posts to fetch
        
    Returns:
        List[Dict]: List of posts with their details
    """
    posts = []
    # seen_posts = set()
    
    for submission in reddit.subreddit("all").search(
        search_query, 
        sort='relevance', 
        time_filter=duration,
        limit=limit
    ):
        if is_promotional(submission) :
            continue
        
        if duration == 'day':
            post_age = datetime.utcnow() - datetime.utcfromtimestamp(submission.created_utc)
            if post_age > timedelta(days=1):
                continue
        
        
        subreddit = submission.subreddit
        
        if subreddit.subscribers < 100:
            continue
        
        normalized_title = "".join(submission.title.lower().split())
            
        author = submission.author.name if submission.author else None
        
        post_identifier = (author, normalized_title)
        
        if post_identifier in seen_posts:
            continue  
        
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
        seen_posts.add(post_identifier)
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
                       secondary_weight: float = 0.3,
                       duration: str="month") -> pd.DataFrame:
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
    if True : 
        return find_relevant_posts_extra(primary_keywords,
                       secondary_keywords,
                       limit, min_similarity)
    
    
    if primary_keywords == [""]:
        primary_keywords = secondary_keywords.copy()
        secondary_keywords = []
        
    print(primary_keywords)
    print(secondary_keywords)
        
    # Create search query from primary keywords
    if len(primary_keywords) == 1:
        search_query = ' OR '.join(f'"{kw}"' for kw in (primary_keywords + secondary_keywords))
    else:
        search_query = ' OR '.join(f'"{kw}"' for kw in primary_keywords)
    
    # Fetch posts using Reddit's search
    all_posts = fetch_reddit_posts(search_query, limit, duration)
    
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



def find_relevant_posts_extra(primary_keywords: List[str],
                       secondary_keywords: List[str],
                       limit: int,
                       min_similarity: float = 0.1,
                       primary_weight: float = 0.7,
                       secondary_weight: float = 0.3,
                       duration: str="month") -> pd.DataFrame:
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
    if primary_keywords == [""]:
        primary_keywords = secondary_keywords.copy()
        secondary_keywords = []
        
    # Create search query from primary keywords
    # if len(primary_keywords) == 1:
    #     search_query = ' OR '.join(f'"{kw}"' for kw in (primary_keywords + secondary_keywords))
    # else:
    #     search_query = ' OR '.join(f'"{kw}"' for kw in primary_keywords)
        
    # primary_chunks = chunk_multi_word_keywords(primary_keywords)
    primary_chunks = list(combinations(primary_keywords, 2))
    print("Primary chunks:", primary_chunks)
    # Fetch posts for each chunk
    all_posts = []
    seen_posts = set()

    
    for chunk in primary_chunks:
        # search_query = create_reddit_search_query(chunk)
        search_query = ' OR '.join(f'"{kw}"' for kw in chunk)
        print("query:", search_query)
        chunk_posts = fetch_reddit_posts(search_query, limit, duration, seen_posts)
        all_posts.extend(chunk_posts)
    
    # Fetch posts using Reddit's search
    # all_posts = fetch_reddit_posts(search_query, limit, duration)
    
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


def chunk_multi_word_keywords(keywords: List[str], max_words: int = 2) -> List[List[str]]:
    # Count words in each keyword
    keyword_word_counts = [(kw, len(kw.split())) for kw in keywords]
    
    chunks = []
    current_chunk = []
    current_word_count = 0
    
    for keyword, word_count in keyword_word_counts:
        # If adding this keyword would exceed max_words, start a new chunk
        if current_word_count + word_count > max_words and current_chunk:
            chunks.append(current_chunk)
            current_chunk = []
            current_word_count = 0
        
        # Add keyword to current chunk
        current_chunk.append(keyword)
        current_word_count += word_count
    
    # Add any remaining keywords in the last chunk
    if current_chunk:
        chunks.append(current_chunk)
        
    return chunks


def create_reddit_search_query(keywords: List[str]) -> str:
    """
    Creates a Reddit-optimized search query from keywords
    """
    processed_queries = []
    
    for keyword in keywords:
        if ' ' in keyword:
            words = keyword.split()
            processed_queries.append(f'"{keyword}"')  # exact phrase
            processed_queries.extend(words)  # individual words
        else:
            processed_queries.append(keyword)
    
    return ' OR '.join(processed_queries)

def chunk_keywords(keywords, chunk_size=2):
    return [keywords[i:i + chunk_size] for i in range(0, len(keywords), chunk_size)]