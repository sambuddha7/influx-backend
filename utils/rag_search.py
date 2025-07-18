from openai import OpenAI
from pinecone import Pinecone
import os 
from dotenv import load_dotenv


client = OpenAI(api_key=os.getenv("OPENAI_KEY"))


pc = Pinecone(api_key=os.getenv("PINECONE_KEY"))
index_host = os.getenv("PINECONE_HOST")
namespace = "test"

import tiktoken

def count_tokens(text: str, model: str = "text-embedding-3-small") -> int:
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))

def upsert_user_docs(user_id: str, docs: list[dict], source_type: str):
    """
    Args:
      user_id: Unique user identifier
      docs: List of dicts, each with 'content' and additional metadata.
    """
    index = pc.Index(host=index_host)

    vectors = []

    for i, doc in enumerate(docs):
        content = doc["content"]
        # title = doc.get("title", f"Untitled_{i}")
        token_count = count_tokens(content)
        # print(f"[DEBUG] Doc {title} has {token_count} tokens")

        if token_count > 8192:
            # print(f"[WARNING] Doc {title} exceeds token limit: {token_count} tokens")
            continue
        embedding_resp = client.embeddings.create(
            model="text-embedding-3-small",
            input=doc["content"]
        )
        embedding = embedding_resp.data[0].embedding

  
        metadata = doc.copy() 
        metadata = {k: (v if v is not None else "") for k, v in doc.items()}
        metadata["user_id"] = user_id

        vector_id = str(user_id) + "_doc" + str(i) + "_" + source_type

        vectors.append({
            "id": vector_id,
            "values": embedding,
            "metadata": metadata
        })

    index.upsert(
        namespace=user_id,
        vectors=vectors
    )
    
    
def query_user_docs(user_id: str, query_text: str, top_k: int = 5):
    """
    Args:
      user_id: Unique user identifier
      query_text: The text to create the query embedding from
      top_k: Number of top results to return
    """
    index = pc.Index(host=index_host)

    # Create embedding for the query text
    embedding_resp = client.embeddings.create(
        model="text-embedding-3-small",
        input=query_text
    )
    query_embedding = embedding_resp.data[0].embedding

    # Query the index, filtering by user_id in metadata
    query_response = index.query(
        namespace=user_id,
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True,
    )

    return query_response


def format_company_docs(docs):
    doc_snippets = []
    for match in docs.get("matches", []):
        content = match.get("metadata", {}).get("content", "")
        if content:
            doc_snippets.append(content.strip())
    return "\n\n".join(doc_snippets)


def get_all_user_docs(user_id: str):
    """
    Retrieve all documents for a specific user from Pinecone
    
    Args:
        user_id: Unique user identifier
    
    Returns:
        List of documents with metadata
    """
    index = pc.Index(host=index_host)
    
    
    dummy_embedding = [0.0] * 1536 
    
    try:
        # Query with a very high top_k to get all docs
        query_response = index.query(
            namespace=user_id,
            vector=dummy_embedding,
            top_k=10000,  # Adjust based on expected max docs per user
            include_metadata=True,
        )
        
        # Extract and format the documents
        documents = []
        for match in query_response.matches:
            doc = {
                "id": match.id,
                "content": match.metadata.get("content", ""),
                "title": match.metadata.get("title", ""),
                "source_type": match.metadata.get("source_type", ""),
                "file_type": match.metadata.get("file_type", ""),
                "file_size": match.metadata.get("file_size", 0),
                "url": match.metadata.get("url", ""),
                "uploaded_at": match.metadata.get("uploaded_at", ""),
                "score": match.score
            }
            documents.append(doc)
        
        # Sort by uploaded_at (most recent first)
        documents.sort(key=lambda x: x.get("uploaded_at", ""), reverse=True)
        
        return documents
        
    except Exception as e:
        print(f"Error retrieving user documents: {e}")
        return []