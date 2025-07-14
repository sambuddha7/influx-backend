# post.py (or web_scrape_router.py)


from fastapi import APIRouter, HTTPException, Query, Body
from utils.web_scraper import scrape_website    
from utils.rag_search import upsert_user_docs, get_all_user_docs

router = APIRouter()

@router.get("/scrape")
def scrape_url(base_url: str = Query(..., description="The website URL to scrape"), 
               user_id: str = Query(..., description="Unique user identifier"),
               source_type: str = Query(..., description="source of the request")):
    print("user id is pls show up",user_id)
    try:
        data = scrape_website(base_url)
        print(data)
        try:
            upsert_user_docs(user_id, data, source_type)
        except Exception as upsert_error:
            print("Upsert failed with error:", repr(upsert_error))
            raise HTTPException(status_code=500, detail=f"Upsert failed: {str(upsert_error)}")

        return {"pages": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    
@router.post("/upsert-docs")
def upsert_documents(user_id: str = Query(..., description="Unique user identifier"),
                    source_type: str = Query(..., description="Source of the request"),
                    request: dict = Body(...)):
    """
    Endpoint to upsert processed documents to vector database
    
    Query parameters:
    - user_id: Unique user identifier
    - source_type: Source of the request (e.g., "upload", "file_upload", etc.)
    
    Expected request body:
    {
        "docs": [
            {
                "content": "extracted text content",
                "title": "filename",
                "file_type": "mime type",
                "file_size": "file size in bytes",
                "uploaded_at": "ISO timestamp"
            }
        ]
    }
    """
    print("user id is pls show up", user_id)
    try:
        docs = request.get("docs", [])
        
        if not docs or not isinstance(docs, list):
            raise HTTPException(status_code=400, detail="docs must be a non-empty list")
        
        print(f"Processing {len(docs)} documents for user: {user_id}")
        
        # Validate document structure
        for i, doc in enumerate(docs):
            if not isinstance(doc, dict):
                raise HTTPException(status_code=400, detail=f"Document {i} must be an object")
            if not doc.get("content"):
                raise HTTPException(status_code=400, detail=f"Document {i} missing required 'content' field")
        
        try:
            upsert_user_docs(user_id, docs, source_type)
            
            return {
                "success": True,
                "message": f"Successfully processed {len(docs)} document(s)",
                "processed_count": len(docs)
            }
            
        except Exception as upsert_error:
            print("Upsert failed with error:", repr(upsert_error))
            raise HTTPException(status_code=500, detail=f"Upsert failed: {str(upsert_error)}")
            
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        print("Unexpected error in upsert_documents:", repr(e))
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    
@router.get("/user-documents")
async def get_user_documents(user_id: str):
    """
    Get all documents for a specific user
    
    Args:
        user_id: User identifier
        source_type: Optional filter by source type (documents, etc.)
    """
    try:
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id is required")
        
        documents = get_all_user_docs(user_id)
        
        seen_titles = set()

        files = []
        urls = []
        
        for doc in documents:
            title = doc.get("title", "")
            if title in seen_titles:
                    continue 
            seen_titles.add(title)

            if doc.get("source_type") == "url":
                urls.append({
                    "id": doc["id"],
                    "url": doc.get("url", ""),
                    "title": doc.get("title", ""),
                    "content": doc.get("content", ""),
                    "uploaded_at": doc.get("uploaded_at", "")
                })
            else:  # file or other types
                files.append({
                    "id": doc["id"],
                    "title": doc.get("title", ""),
                    "content": doc.get("content", ""),
                    "file_type": doc.get("file_type", ""),
                    "file_size": doc.get("file_size", 0),
                    "uploaded_at": doc.get("uploaded_at", ""),
                    "url": doc.get("url", "")

                })
        
        return {
            "files": files,
            "urls": urls,
            "total": len(documents)
        }
        
    except Exception as e:
        print(f"Error in get_user_documents endpoint: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve documents")