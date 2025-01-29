from fastapi import APIRouter
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


def get_keywords(description):
    system_prompt = "Generate keywords from the given text in a csv format. "
    user_prompt = f"""
    
    <instructions>
1. Please generate 10 keywords from the following company description:\n\n{description}
2. Provide just the csv, without any additional text or explanations.
3. Here's a sample of a reply : "keyword1, keyword2, keyword3, keyword4, keyword5, keyword6, keyword7, keyword8, keyword9, keyword10"
</instructions>
    
    """
    try:
        message = client.messages.create(
            model="claude-3-haiku-latest",
            system=system_prompt,
            max_tokens=1000,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )

        string = message.content[0].text
        cleaned_string = string.strip('"')

        return cleaned_string
    except Exception as e:
        return f"Error getting summary: {str(e)}"
def get_reply(text_to_reply, company_name, company_description, user_role, sample_replies, marketing_objectives):
    
    marketing_objectives = ""
    system_prompt = f"You are an AI assistant trained to craft personalized Reddit comment replies for {company_name} and finding potential customers."
    if user_role:
        system_prompt = f" You are a {user_role} at {company_name} who is crafting personalized Reddit comment replies and finding potential customers."
    print(system_prompt)
    # if user_role:
        # system_prompt = f"You are an AI assistant trained to craft personalized Reddit comment replies for {company_name}. You can mention that you are a {user_role} at {company_name} but say it as a disclaimer in the end."
    user_prompt = f"""Please generate a Reddit comment reply based on the following inputs:

Text to reply to:
{text_to_reply}

<company_description>{company_description}</company_description>

<instructions>
1. Craft a response that is helpful and adds value to the conversation.
2. Keep the response in one or two lines maximum.
3. Use markdown formatting for better readability if appropriate.
4. Provide just the reply, without any additional text or explanations.
5. Sound genuine and authentic.
6. Use company description or any knowledge you have of the company for reference when mentioning the company.
7. Keep it brief and to the point.
8. Don't mention other companies outside of {company_name} if you're mentioning any company or software.
9. Keep the tone casual, how it is usually on reddit. Don't make it sound formal at all.
</instructions>


"""



    if marketing_objectives:
        user_prompt += f"\n<marketing_objectives>{marketing_objectives}</marketing_objectives>"
        user_prompt += "\n9. Subtly align the response with the marketing objectives."

    if sample_replies:
        user_prompt += f"\n<sample_responses>\n{sample_replies}\n</sample_responses>"
        user_prompt += "\n10. Use the sample responses as a guide for style and content, but don't copy them directly."

    user_prompt += "\n\nPlease generate a Reddit comment reply based on these inputs."
    try:
        message = client.messages.create(
            # model="claude-3-opus-20240229",
            model="claude-3-5-sonnet-latest",
            # model="claude-3-haiku-20240307",
            system=system_prompt,
            max_tokens=1000,
            # messages=[
            #     {
            #         "role": "user",
            #         "content": f"{prompt}\n\nText to reply to:\n{text_to_reply}"
            #     }
            # ]
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )

        string = message.content[0].text
        cleaned_string = string.strip('"')

        return cleaned_string
    except Exception as e:
        return f"Error getting summary: {str(e)}"
    

########################################################################

# add a filter posts feature here through some llm

########################################################################
