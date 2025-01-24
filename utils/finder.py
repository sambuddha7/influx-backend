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

def get_reply(text_to_reply, userid):
    
    company_name = "leadbeam"
    company_description = "Leadbeam.ai is an innovative Outside Sales Intelligence platform that revolutionizes field sales operations. It addresses key pain points by integrating Voice AI, Image, and Location intelligence to streamline data entry, saving reps an average of 5 hours per week. The platform offers real-time CRM updates, intelligent lead generation, and automated follow-ups. Leadbeam tackles inefficient data entry, poor CRM data hygiene, lack of real-time visibility, and ineffective territory management. By automating routine tasks and providing AI-driven tools, it empowers sales teams to work more efficiently, close more deals, and drive revenue growth while maintaining the crucial human connection in field sales."
    user_role = "CEO"
    pain_points = ""
    marketing_objectives = ""
    sample_replies = """
1. "Use hubspot free, then Leadbeam.ai since your reps aren't behind a computer. This gives you the ability to leave a voice note and have HubSpot, follow ups, and your next steps updated."

2. "You should just use Leadbeam.ai with one of your legacy providers like Salesforce or HubSpot. It'll be much simpler and is completely configurable."

3. "Maybe give OAKI a try! We have a free trial, and we used to be a data science company (the tech/ML algorithms we use to match people with jobs are a huge improvement over anything out there right now)."
"""
    system_prompt = f"You are an AI assistant trained to craft personalized Reddit comment replies for {company_name}. Your responses should be helpful, relevant, and subtly promote the company's products without being overtly salesy. always put a disclaimer that you're affiliated with the company."

    if user_role:
        system_prompt = f"You are an AI assistant trained to craft personalized Reddit comment replies for {company_name} but you should reply as the {user_role} and maintain a tone consistent with this role. you can either put a disclaimer that you're affiliated with the company or just naturally bring it in your reply. Your responses should be helpful, relevant, and subtly promote the company's products without being overtly salesy."
    user_prompt = f"""Please generate a Reddit comment reply based on the following inputs:

Text to reply to:
{text_to_reply}

<instructions>
1. Craft a response that is helpful and adds value to the conversation.
2. Keep the response between 150-400 characters.
3. Use markdown formatting for better readability if appropriate.
4. Provide just the reply, without any additional text or explanations.
5. Sound genuine and authentic.
</instructions>
"""

    if pain_points:
        user_prompt += f"\n<pain_points>{pain_points}</pain_points>"
        user_prompt += "\n6. Address the specified pain points in your response."

    if marketing_objectives:
        user_prompt += f"\n<marketing_objectives>{marketing_objectives}</marketing_objectives>"
        user_prompt += "\n7. Subtly align the response with the marketing objectives."

    if sample_replies:
        user_prompt += f"\n<sample_responses>\n{sample_replies}\n</sample_responses>"
        user_prompt += "\n8. Use the sample responses as a guide for style and content, but don't copy them directly."

    user_prompt += "\n\nPlease generate a Reddit comment reply based on these inputs."
    try:
        message = client.messages.create(
            # model="claude-3-opus-20240229",
            model="claude-3-haiku-20240307",
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
