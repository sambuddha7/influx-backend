# post.py (or web_scrape_router.py)

from fastapi import APIRouter, HTTPException, Query
from utils.web_scraper import scrape_website, scrape_home_and_about   

router = APIRouter()

@router.get("/scrape")
def scrape_url(base_url: str = Query(..., description="The website URL to scrape")):
    try:
        data = scrape_home_and_about(base_url)
        return {"pages": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
