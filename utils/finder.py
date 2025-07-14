from fastapi import APIRouter
import os
from dotenv import load_dotenv
import praw
from anthropic import Anthropic
from datetime import datetime
import pandas as pd
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
    posts = []
    
    for post in rising_posts:
        posts.append({
            'id': post.id,
            'title': post.title,
            'body': post.selftext,
            'url': f"https://reddit.com{post.permalink}",
            'score': post.score,
            'created_utc': datetime.fromtimestamp(post.created_utc),
            'num_comments': post.num_comments,
            'subreddit': post.subreddit.display_name
        })
    
    return pd.DataFrame(posts)

def get_hot_posts(subreddit_name, limit=5):
    subreddit = reddit.subreddit(subreddit_name)
    hot_posts = subreddit.hot(limit=limit)
    posts = []
    
    for post in hot_posts:
        posts.append({
            'id': post.id,
            'title': post.title,
            'body': post.selftext,
            'url': f"https://reddit.com{post.permalink}",
            'score': post.score,
            'created_utc': datetime.fromtimestamp(post.created_utc),
            'num_comments': post.num_comments,
            'subreddit': post.subreddit.display_name
        })
    
    return pd.DataFrame(posts)

def get_description(content):
    system_prompt = "Generate a company description from the given text. "
    user_prompt = f"""
    
    <instructions>
1. I have given the content of a company's home page and maybe the about page, generate a 50 - 100 word company description
2. Emphasise on what the company does, what their industry is, maybe some solutions.
3. This is what we scraped from their website: {content}
4. provide just the description, nothing else.
5. If it is a large fortune 500 company that you already know about don't rely on the scraped pages for information.
6. Focus on what the company does and the industry rather than work culture etc.
7. Write your description in a tone that you would put on the company website if you were them
8. If there is no text given just generate a description from your knowledge of the company name
9. if you don't know anything about the company and the text is blank just return nothing.
10. Even if you're not confident about the description generate something.
</instructions>
    
    """
    print(f"generating user description with the following prompt: {user_prompt}")
    try:
        message = client.messages.create(
            model="claude-3-5-haiku-20241022",
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
def get_subreddits(description):
    system_prompt = "Give subreddits from the given text in a csv format. "
    user_prompt = f"""
    
    <instructions>
Here is the company description:

<company_description>
{description}
</company_description>

You are a marketing specialist tasked with generating subreddit recommendations for this company. Your goal is to identify 20 different subreddits that are relevant to the company, its products, services, target audience, or industry.

Instructions:
1. Read and analyze the company description carefully.
2. Based on the company's key aspects (products, services, target audience, industry, verticals, competitors etc.), identify 20 relevant subreddits.
3. Ensure the subreddits cover a diverse range to maximize reach and engagement potential.
4. Focus on subreddits likely to contain discussions related to the company's products, services, or industry.
5. Avoid suggesting subreddits that are too broad or only tangentially related to the company's focus.


Output Requirements:
- After your analysis, provide ONLY a single line of 20 comma-separated subreddit names.
- Do NOT include the "r/" prefix in the subreddit names.
- Do NOT include any additional text, explanations, or analysis in the final output.

Example output format:
marketing,smallbusiness,entrepreneur,techstartups,b2bsales,saas,productivity,remotework,businessstrategy,startup,technology,artificialintelligence,machinelearning,datascience,businessintelligence

Your task is to generate a similar list based on the provided company description. Remember, your final output should be ONLY the CSV list of subreddit names, nothing else.
</instructions>
    
    """
    try:
        message = client.messages.create(
            model="claude-3-5-haiku-latest",
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
        return f"Error getting subreddits: {str(e)}"
def get_phrases(description):
    system_prompt = "Generate phrases from the given text in a csv format. Your task is to generate paraphrased pain point phrases that real potential customers might express online (e.g., Reddit, forums, Slack, or surveys)."
    user_prompt = f"""
    
    <instructions>
1. Please generate at least 10 paraphrased pain point statements from the following company description:\n\n{description}
2. Provide just the csv, without any additional text or explanations.
3. Vary the tone, structure, and style — include casual questions, frustrations, short complaints, or requests for help. Mimic how real users talk online
4. Here's a sample of a reply : "example reply 1, example reply 2, example reply 3"

</instructions>
    
    """
    try:
        message = client.messages.create(
            model="claude-3-5-haiku-20241022",
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
        return f"Error getting keywords: {str(e)}"
def get_keywords(description):
    system_prompt = "Generate keywords from the given text in a csv format. "
    user_prompt = f"""
    
    <instructions>
1. Please generate 20 keywords from the following company description:\n\n{description}
2. Provide just the csv, without any additional text or explanations.
3. Don't give too industry specific keywords but have a good mix of common words as well.
4. Give either one or two keywords max.
5. Here's a sample of a reply : "keyword1, keyword2, keyword3, keyword4, keyword5, keyword6, keyword7, keyword8, keyword9, keyword10"
</instructions>
    
    """
    try:
        message = client.messages.create(
            model="claude-3-5-haiku-20241022",
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
        return f"Error getting keywords: {str(e)}"
def get_reply_comm(text_to_reply, company_name, company_description, user_role, sample_replies, marketing_objectives):
    
    marketing_objectives = ""
    system_prompt = f"You are a brand strategy employee trained to craft personalized Reddit comment replies for {company_name} and look like an experienced professional in that field."
    if user_role:
        system_prompt = f" You are a {user_role} at {company_name} who is crafting personalized Reddit comment replies and look like an experienced professional in that field."
    print(system_prompt)
    # if user_role:
        # system_prompt = f"You are an AI assistant trained to craft personalized Reddit comment replies for {company_name}. You can mention that you are a {user_role} at {company_name} but say it as a disclaimer in the end."
    user_prompt = f"""Please generate a Reddit comment reply based on the following inputs:

Text to reply to:
{text_to_reply}

<company_description>{company_description}</company_description>

<instructions>
1. Craft a response that is helpful and adds value to the conversation.
2. Keep the response in one or two lines, but if its appropriate you can make it longer. 
3. Use markdown formatting for better readability if appropriate.
4. Provide just the reply, without any additional text or explanations.
5. Sound genuine and authentic.
6. You can give a longer reply if you're trying to mention a personal experience.
7. Keep it brief and to the point.
8. Keep the tone casual, how it is usually on reddit. Don't make it sound formal at all.
9. If you're mentioning a different company, make sure to mention you're not affiliated with them.
</instructions>


"""



   
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
def get_reply_feedback(initial_reply, feedback, post_title, post_content, subreddit):
    system_prompt = """You help generate authentic Reddit replies. This prompt you are regenerating a comment, incorporate it naturally while maintaining an authentic, conversational tone that fits the specific subreddit and post context."""
    
    user_prompt = f"""ORIGINAL POST CONTEXT:
    Subreddit: r/{subreddit}
    Title: {post_title}
    Content: {post_content}

    CURRENT REPLY: {initial_reply}

    REPLY TYPES GUIDE:
    - "Add Value": Make the reply more helpful, informative, and useful to the original poster
    - "Ask a Question": Include a thoughtful follow-up question to encourage discussion
    - "Relatable": Add personal experiences or shared understanding to connect with the poster
    - "Soft Plug": Subtly and naturally mention relevant products/services without being pushy

    ADDITIONAL COMMENTS TO INCORPORATE: {feedback}

    <instructions>
    1. Consider the post's context, tone, and the subreddit culture when modifying the reply
    2. Incorporate the feedback naturally while ensuring the reply still addresses the original post appropriately
    3. If feedback includes a type like "Add Value", "Ask a Question", "Relatable", or "Soft Plug", apply that approach while staying relevant to the original post
    4. Maintain authenticity - the reply should sound natural and genuinely helpful to the original poster
    5. Keep the tone appropriate for the subreddit (professional for business subs, casual for general discussion, etc.)
    6. Provide just the improved reply, without any additional text or explanations
    7. Don't market anything unless feedback type is soft plug
    8. Rewrite the reply from scratch unless additional comments include minor tweaks to the generated reply.
    9. Keep the response in one or two line unless mentioned by the user to make it longer.
    </instructions>
    """
    print(user_prompt)
    try:
        message = client.messages.create(
            model="claude-3-5-sonnet-latest",
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
10. No emojis
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
def filter_best_subreddits(subreddit_list, company_description, num_subreddits=10):
    """
    Filter and select the best subreddits for marketing a company based on its description.
    
    Args:
        subreddit_list (list or set): List of subreddit names to filter
        company_description (str): Description of the company to market
        num_subreddits (int): Number of subreddits to return (default: 10)
        
    Returns:
        list: List of best subreddits in the requested format
    """
    system_prompt = "You are an AI marketing expert specializing in Reddit marketing strategy."
    
    user_prompt = f"""Please analyze the following list of subreddits and select exactly {num_subreddits} that would be best for marketing a company based on the description provided.

<company_description>
{company_description}
</company_description>

<subreddit_list>
{', '.join(sorted(subreddit_list))}
</subreddit_list>

<instructions>
1. Select exactly {num_subreddits} subreddits from the provided list that would be most relevant for marketing the described company.
2. Include a good mix of large/popular subreddits and smaller/medium-sized ones for a balanced marketing approach.
3. Only select subreddits from the provided list.
4. Return ONLY a Python set literal containing your selections, in exactly this format: {{'subreddit1', 'subreddit2', 'subreddit3'}}
5. Do not include any explanation, introduction, or additional text.
</instructions>
"""
    
    try:
        message = client.messages.create(
            model="claude-3-5-sonnet-latest",
            system=system_prompt,
            max_tokens=1000,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )
        
        response = message.content[0].text.strip()
        return response
            
    except Exception as e:
        return f"Error filtering subreddits: {str(e)}"