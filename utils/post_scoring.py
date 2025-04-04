import pandas as pd
import torch
from sentence_transformers import SentenceTransformer, util
from transformers import pipeline
import gc
import multiprocessing

def wrap_df(reddit_posts):
    columns = ["id", "subreddit", "title", "body", "llm_reply", "url", "created_utc"]
    df = pd.DataFrame(reddit_posts, columns=columns)
    df["full text"] = df["title"] + " " + df["body"]
    return df

def add_semantic_relevance_score(df, company_desc, model_name="all-MiniLM-L6-v2"):
    """
    Computes semantic relevance scores in batch.
    """
    model = SentenceTransformer(model_name)
    
    # Compute the embedding for the company description only once
    company_embedding = model.encode(company_desc, convert_to_tensor=True, show_progress_bar=False)
    
    # Batch compute embeddings for all posts using torch.no_grad() to save memory
    with torch.no_grad():
        post_texts = df["full text"].tolist()
        post_embeddings = model.encode(post_texts, convert_to_tensor=True, show_progress_bar=False)
    
    # Compute cosine similarities; since company_embedding is a single vector,
    # the result is a (n, 1) tensor.
    scores = util.cos_sim(post_embeddings, company_embedding)
    df["semantic_score"] = scores.squeeze().cpu().numpy()
    return df

# def add_sentiment_intent_analysis(df):
#     """
#     Adds sentiment and intent analysis by processing texts in batches.
#     """
#     # Initialize pipelines once
#     sentiment_pipeline = pipeline("sentiment-analysis")
#     zero_shot_pipeline = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
#     candidate_labels = ["problem statement", "seeking recommendation", "discussion", "off-topic"]

#     texts = df["full text"].tolist()

#     # Batch process sentiment analysis
#     sentiment_results = sentiment_pipeline(texts, batch_size=16)
#     sentiment_labels = [res["label"] for res in sentiment_results]
#     sentiment_scores = [res["score"] for res in sentiment_results]

#     # Batch process zero-shot classification for intent analysis
#     intent_results = zero_shot_pipeline(texts, candidate_labels=candidate_labels, batch_size=16)
#     intent_labels = [res["labels"][0] for res in intent_results]
#     intent_scores = [res["scores"][0] for res in intent_results]

#     df["sentiment"] = sentiment_labels
#     df["sentiment_score"] = sentiment_scores
#     df["intent"] = intent_labels
#     df["intent_score"] = intent_scores

#     return df
def add_sentiment_intent_analysis(df):
    """
    Adds sentiment and intent analysis by processing texts in batches.
    Cleans up models to prevent leaked semaphores on shutdown.
    """
    # Initialize pipelines
    sentiment_pipeline = pipeline("sentiment-analysis")
    zero_shot_pipeline = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
    candidate_labels = ["problem statement", "seeking recommendation", "discussion", "off-topic"]

    texts = df["full text"].tolist()

    # Sentiment
    sentiment_results = sentiment_pipeline(texts, batch_size=16)
    sentiment_labels = [res["label"] for res in sentiment_results]
    sentiment_scores = [res["score"] for res in sentiment_results]

    # Intent
    intent_results = zero_shot_pipeline(texts, candidate_labels=candidate_labels, batch_size=16)
    intent_labels = [res["labels"][0] for res in intent_results]
    intent_scores = [res["scores"][0] for res in intent_results]

    # Add to df
    df["sentiment"] = sentiment_labels
    df["sentiment_score"] = sentiment_scores
    df["intent"] = intent_labels
    df["intent_score"] = intent_scores

    # ✨ CLEANUP to avoid semaphore warnings
    del sentiment_pipeline
    del zero_shot_pipeline
    torch.cuda.empty_cache()  # just in case, even if you're on CPU
    gc.collect()

    return df

def add_final_promo_score(df, weights=None, boost_map=None):
    """
    Calculates a final promotional score for each post based on:
      - semantic_score
      - intent_score (with boost for valuable intent types)
      - sentiment_score (positive adds, negative subtracts)
    """
    if weights is None:
        weights = {
            "semantic": 0.4,
            "intent": 0.4,
            "sentiment": 0.2
        }
    if boost_map is None:
        boost_map = {
            "seeking recommendation": 1.5,
            "problem statement": 1.3
        }

    def compute_score(row):
        # Normalize intent label and apply boost if applicable
        intent_label = row["intent"].lower()
        intent_multiplier = boost_map.get(intent_label, 1.0)
        intent_component = row["intent_score"] * intent_multiplier

        # Apply sentiment multiplier: add for positive, subtract for negative
        sentiment_multiplier = 1 if row["sentiment"].upper() == "POSITIVE" else -1
        sentiment_component = row["sentiment_score"] * sentiment_multiplier

        # Combine weighted components
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
    df = add_semantic_relevance_score(df, company_description)
    df = add_sentiment_intent_analysis(df)
    df = add_final_promo_score(df)

    id_to_score = dict(zip(df["id"], df["promo_score"]))
    for post in reddit_posts:
        post_id = post[0]
        promo_score = id_to_score.get(post_id, 0)
        post.append(promo_score)

    # Final GC cleanup
    gc.collect()

    return reddit_posts