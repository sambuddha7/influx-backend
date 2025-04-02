import pandas as pd
from sentence_transformers import SentenceTransformer, util
from transformers import pipeline


def wrap_df(reddit_posts):
    columns = ["id", "subreddit", "title", "body", "llm_reply", "url", "created_utc"]
    df = pd.DataFrame(reddit_posts, columns=columns)
    df["full text"] = df["title"] + " " + df["body"]
    return df

def add_semantic_relevance_score(df, company_desc, model_name="all-MiniLM-L6-v2"):
    """
    Computes a semantic relevance score for each post in the DataFrame
    by comparing the post's full text with the company description.

    Parameters:
    - df (pandas.DataFrame): DataFrame containing a 'full text' column.
    - company_desc (str): A string describing the company's product or service.
    - model_name (str): The name of the SentenceTransformer model to use.

    Returns:
    - df (pandas.DataFrame): The DataFrame with an added 'semantic_score' column.
    """
    # Initialize the model
    model = SentenceTransformer(model_name)
    
    # Compute embedding for the company description once
    company_embedding = model.encode(company_desc, convert_to_tensor=True)
    
    # Define a helper function to compute cosine similarity for a given text
    def compute_score(text):
        post_embedding = model.encode(text, convert_to_tensor=True)
        # Compute cosine similarity between the post and company embeddings
        score = util.cos_sim(post_embedding, company_embedding)
        return float(score)
    
    # Apply the helper function to the 'full text' column
    df["semantic_score"] = df["full text"].apply(compute_score)
    
    return df
def add_sentiment_intent_analysis(df):
    """
    Adds sentiment and intent analysis to the DataFrame by applying NLP pipelines
    to the 'full text' column. It adds the following columns:
    - 'sentiment': The sentiment label (e.g., POSITIVE or NEGATIVE)
    - 'sentiment_score': The confidence score of the sentiment
    - 'intent': The top predicted intent label (e.g., problem statement, seeking recommendation, discussion, off-topic)
    - 'intent_score': The confidence score for the intent prediction
    
    Parameters:
    - df (pandas.DataFrame): DataFrame containing a 'full text' column.
    
    Returns:
    - df (pandas.DataFrame): The DataFrame with added sentiment and intent columns.
    """
    # Initialize the sentiment analysis pipeline
    sentiment_pipeline = pipeline("sentiment-analysis")
    
    # Initialize the zero-shot classification pipeline for intent analysis
    # Here we use the Facebook BART large MNLI model.
    zero_shot_pipeline = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
    
    # Define candidate intent labels (modify these as needed)
    candidate_labels = ["problem statement", "seeking recommendation", "discussion", "off-topic"]

    def analyze_text(text):
        # Get sentiment prediction
        sentiment_result = sentiment_pipeline(text)[0]
        sentiment_label = sentiment_result["label"]
        sentiment_score = sentiment_result["score"]
        
        # Get intent prediction using zero-shot classification
        intent_result = zero_shot_pipeline(text, candidate_labels)
        intent_label = intent_result["labels"][0]      # top label
        intent_score = intent_result["scores"][0]        # its confidence score
        
        return sentiment_label, sentiment_score, intent_label, intent_score

    # Apply the analysis to each row in the 'full text' column
    results = df["full text"].apply(analyze_text)
    
    # Unpack the results into new columns
    df["sentiment"], df["sentiment_score"], df["intent"], df["intent_score"] = zip(*results)
    
    return df

#final score of the post
def add_final_promo_score(df, weights=None, boost_map=None):
    """
    Calculates a final promotional score for each post based on:
    - semantic_score
    - intent_score (boosted for 'seeking recommendation' or 'problem statement')
    - sentiment_score (boosted for positive, penalized for negative)

    Parameters:
    - df (pandas.DataFrame): Must contain 'semantic_score', 'intent_score', 'sentiment', and 'sentiment_score'.
    - weights (dict, optional): Custom weights for each component.
    - boost_map (dict, optional): Boost multipliers for specific intents.

    Returns:
    - df (pandas.DataFrame): With a new 'promo_score' column.
    """
    if weights is None:
        weights = {
            "semantic": 0.4,
            "intent": 0.4,
            "sentiment": 0.2
        }

    if boost_map is None:
        # Boost 'seeking recommendation' more than 'problem statement'
        boost_map = {
            "seeking recommendation": 1.5,
            "problem statement": 1.3
        }

    def compute_score(row):
        # Normalize intent label
        intent_label = row["intent"].lower()

        # Boost intent if it matches one of our valuable types
        intent_multiplier = boost_map.get(intent_label, 1.0)
        intent_component = row["intent_score"] * intent_multiplier

        # Handle sentiment
        sentiment_multiplier = 1 if row["sentiment"].upper() == "POSITIVE" else -1
        sentiment_component = row["sentiment_score"] * sentiment_multiplier

        # Combine all components
        final_score = (
            weights["semantic"] * row["semantic_score"] +
            weights["intent"] * intent_component +
            weights["sentiment"] * sentiment_component
        )

        return final_score

    df["promo_score"] = df.apply(compute_score, axis=1)
    return df

def final_df(reddit_posts, company_description):
    df = wrap_df(reddit_posts)
    print(df)
    df = add_semantic_relevance_score(df, company_description)
    df = add_sentiment_intent_analysis(df)
    df = add_final_promo_score(df)  # or pass a custom boost_map if you want
    print(df[["title", "semantic_score", "intent", "intent_score", "sentiment", "sentiment_score", "promo_score"]]
        .sort_values(by="promo_score", ascending=False))

    id_to_score = dict(zip(df["id"], df["promo_score"]))  # Create a mapping from post ID to score

    # Append promo_score to each reddit post object
    for post in reddit_posts:
        post_id = post[0]  # post[0] = id
        promo_score = id_to_score.get(post_id, 0)
        post.append(promo_score)  # Add promo_score as the 8th item

    return reddit_posts  # Return the updated list