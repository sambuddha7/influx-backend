
import os
from dotenv import load_dotenv
import praw
from anthropic import Anthropic

load_dotenv()


reddit = praw.Reddit(
    client_id=os.getenv("CLIENT_ID"),
    client_secret=os.getenv("CLIENT_SECRET"),
    user_agent=os.getenv("USER_AGENT"),
)


client = Anthropic(
    api_key=os.getenv("CLAUDE_API_KEY"),
)



def get_rising_posts(subreddit_name, limit=5):
    subreddit = reddit.subreddit(subreddit_name)
    rising_posts = subreddit.rising(limit=limit)
    return [[post.id, post.title, post.selftext] for post in rising_posts]


# for multiple subreddits "subreddit1+subreddit2"
def get_hot_posts(subreddit_name, limit=5):
    subreddit = reddit.subreddit(subreddit_name)
    hot_posts = subreddit.hot(limit=limit)
    return [[post.id, post.title, post.selftext] for post in hot_posts]

def get_reply(text_to_summarise):
    try:
        prompt = "Please provide a reply of the following reddit post in 2-3 sentences. Make sure to sound genuine and authentic and maybe if you can draw from experiences do that. just give the reply directly"
        message = client.messages.create(
            # model="claude-3-opus-20240229",
            model="claude-3-haiku-20240307",
            max_tokens=1000,
            messages=[
                {
                    "role": "user",
                    "content": f"{prompt}\n\nText to summarize:\n{text_to_summarise}"
                }
            ]
        )
        return message.content[0].text
    except Exception as e:
        return f"Error getting summary: {str(e)}"
    

########################################################################

# add a filter posts feature here through some llm

########################################################################
