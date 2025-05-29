# post.py (or web_scrape_router.py)

from fastapi import APIRouter, HTTPException, Query
from utils.web_scraper import scrape_website    
from utils.rag_search import upsert_user_docs
router = APIRouter()

@router.get("/scrape")
def scrape_url(base_url: str = Query(..., description="The website URL to scrape"), 
               user_id: str = Query(..., description="Unique user identifier")):
    print("user id is pls show up",user_id)
    try:
        data = scrape_website(base_url)
        try:
            upsert_user_docs(user_id, data)
        except Exception as upsert_error:
            print("Upsert failed with error:", repr(upsert_error))
            raise HTTPException(status_code=500, detail=f"Upsert failed: {str(upsert_error)}")
        return {"pages": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
