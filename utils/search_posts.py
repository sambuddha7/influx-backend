import asyncpraw
import asyncio
import nest_asyncio
from datetime import datetime
import time
import re



##################################################

# main search function

##################################################

async def search_reddit_stream(
    reddit,
    keywords,
    target_subreddits=None,
    max_posts=1000
):
    """
    Stream 'new' posts from Reddit and filter locally by keywords.

    :param reddit: AsyncPRAW Reddit instance
    :param keywords: list of strings to match in title+body
    :param target_subreddits: list of subreddit names (defaults to 'all')
    :param max_posts: integer, stop after this many matched posts
    :returns: list of post dicts
    """
    cutoff = time.time() - 24 * 3600
    big_cutoff = time.time() - 3 * 86400 
    subreddits = '+'.join(target_subreddits) if target_subreddits else 'all'
    collected = []
    seen_ids = set()
    post_counter = 0

    print(f" Streaming r/{subreddits}.new() and filtering for keywords...")

    try:
        filtered_len = 0
        subreddit = await reddit.subreddit(subreddits)
        print(subreddit)
        async for submission in subreddit.new(limit=max_posts * 10):
            if submission.created_utc < big_cutoff:
                    break
            try:
                if submission.created_utc < cutoff:
                  continue
                post_counter += 1
                if post_counter % 100 == 0:
                  print(f" Processed {post_counter} posts so far...")


                text = (submission.title + " " + submission.selftext).lower()

                if text_matches_keywords(text, keywords):
                    if is_promotional(submission):  
                        filtered_len += 1
                        continue  # Skip promotional posts
                    if submission.id not in seen_ids:
                        seen_ids.add(submission.id)
                        collected.append({
                            "id": submission.id,
                            "title": submission.title,
                            "body": submission.selftext,
                            "url": f"https://reddit.com{submission.permalink}",
                            "score": submission.score,
                            "created_utc": datetime.fromtimestamp(submission.created_utc),
                            "num_comments": submission.num_comments,
                            "subreddit": submission.subreddit.display_name
                        })
                        if len(collected) >= max_posts:
                            print(f" Reached max_posts={max_posts}; done.")
                            break
            except Exception as post_err:
                print(f" Error processing post: {post_err}")
    except Exception as stream_err:
        print(f" Error streaming posts from r/{subreddits}: {stream_err}")

    print(f" Finished – Total posts checked: {post_counter}")
    print(filtered_len, "posts filtered out as promotional")
    return collected




##################################################

# helper functions

##################################################

def text_matches_keywords(text, keywords):
    words = set(re.findall(r'\b\w+\b', text.lower()))
    for kw in keywords:
        kw_words = set(kw.lower().split())
        if kw_words.issubset(words):
            return True
    return False


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
                               
        if not body_lower:

            return True  
        
        if len(body_lower) > 2500 : 
            print(len(body_lower))
            return True
               
        return False
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


