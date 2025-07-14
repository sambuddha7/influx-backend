from openai import OpenAI
from pinecone import Pinecone, ServerlessSpec
import time
import tiktoken
from dotenv import load_dotenv
import os

tokenizer = tiktoken.encoding_for_model("text-embedding-ada-002")
OPENAI_API_KEY = os.getenv("VANSH_OPENAI_API_KEY")
openai = OpenAI(api_key=OPENAI_API_KEY)


##################################################
# sentiment analysis functions
##################################################
def get_query_embedding(text):
    response = openai.embeddings.create(
        model="text-embedding-ada-002",
        input=[text]
    )
    return response.data[0].embedding

#main function
def search_relevant_posts_by_phrases(phrases, index, threshold=0.78):
    all_results = []
    seen_ids = set()

    for phrase in phrases:
        query_vector = get_query_embedding(phrase)

        results = index.query(
            vector=query_vector,
            top_k=100,
            include_metadata=True
        )

        for match in results['matches']:
            if match['score'] >= threshold and match['id'] not in seen_ids:
                seen_ids.add(match['id'])
                all_results.append({
                    'score': match['score'],
                    'title': match['metadata'].get('title', ''),
                    'content': match['metadata'].get('content', ''),
                    'url': match['metadata'].get('url', ''),
                    'query_phrase': phrase
                })

    # Now print all collected and deduplicated results
    if not all_results:
        print("❌ No relevant posts found above threshold.")
    else:
        print(f"✅ Found {len(all_results)} unique relevant posts across all phrases:\n")
        for result in all_results:
            print(f"🔍 Matched from query: \"{result['query_phrase']}\"")
            print(f"📌 Score: {result['score']:.4f}")
            print(f"🔗 Title: {result['title']}")
            print(f"📝 Content: {result['content'][:300]}...")
            print(f"🔗 URL: {result['url']}")
            print("-" * 50)
##################################################
# upsert vectors into Pinecone
##################################################

def batch_upsert(index, vectors, namespace, batch_size=50):
    for i in range(0, len(vectors), batch_size):
        batch = vectors[i:i + batch_size]
        try:
            index.upsert(vectors=batch, namespace=namespace)
            print(f"✅ Upserted batch {i//batch_size + 1} ({len(batch)} vectors) to namespace {namespace}")
        except Exception as e:
            print(f"❌ Failed to upsert batch {i//batch_size + 1} to namespace {namespace}: {e}")

##################################################
# helper functions
##################################################

def get_embedding(text, retries=3):
    for attempt in range(retries):
        try:
            response = openai.embeddings.create(
                model="text-embedding-ada-002",
                input=[text]
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Retry {attempt + 1} due to error: {e}")
            time.sleep(1)
    raise Exception("Embedding failed after multiple retries")

def truncate_to_token_limit(text, max_tokens=8000):
    tokens = tokenizer.encode(text)
    if len(tokens) > max_tokens:
        tokens = tokens[:max_tokens]
    return tokenizer.decode(tokens)

def prepare_vector(post):
    # Combine title and content
    text_to_embed = f"{post[2]} - {post[3]}"

    # ✅ Truncate based on tokens, not characters
    safe_text = truncate_to_token_limit(text_to_embed, max_tokens=8000)

    # Embed the text
    embedding = get_embedding(safe_text)

    # Truncate content in metadata if needed (character-level fine here)
    metadata = {
        "title": post[2],
        "content": post[3][:1000],
        "url": post[5],
        "subreddit": post[1],
        "created_utc": str(post[6])
    }

    return (str(post[0]), embedding, metadata)