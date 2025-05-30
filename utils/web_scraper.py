import requests
from bs4 import BeautifulSoup
from newspaper import Article
from urllib.parse import urljoin
import json
from datetime import datetime

def fetch_html(url):
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()
    return response.text

def extract_links(base_url, html):
    soup = BeautifulSoup(html, 'html.parser')
    links = set()
    for tag in soup.find_all("a", href=True):
        full_url = urljoin(base_url, tag['href'])
        if base_url in full_url:
            links.add(full_url)
    return list(links)

def extract_article(url):
    try:
        article = Article(url)
        article.download()
        article.parse()
        return {
            "title": article.title,
            "content": article.text,
            "date_published": str(article.publish_date.date()) if article.publish_date else None
        }
    except Exception as e:
        print(f"[!] Skipping {url} — {e}")
        return None
    
def identify_page_type(url):
    if "about" in url.lower():
        return "about"
    elif "blog" in url.lower() or "article" in url.lower():
        return "blog_post"
    elif "contact" in url.lower():
        return "contact"
    else:
        return "general"

def scrape_home_and_about(base_url):
    if not base_url.startswith("http://") and not base_url.startswith("https://"):
        base_url = "https://" + base_url
    print(f"Scraping home and about pages from: {base_url}")

    pages_to_try = ["/", "/about", "/about-us", "/aboutus"]
    visited = set()
    all_data = []

    for path in pages_to_try:
        full_url = urljoin(base_url, path)
        if full_url in visited:
            continue
        visited.add(full_url)

        try:
            article_data = extract_article(full_url)
            if article_data and len(article_data["content"]) > 200:
                all_data.append({
                    "url": full_url,
                    "page_type": identify_page_type(full_url),
                    "title": article_data["title"],
                    "content": article_data["content"],
                    "date_published": article_data["date_published"]
                })
        except Exception as e:
            print(f"[!] Could not fetch {full_url} — {e}")

    print("home/about scraping done")
    return all_data


def scrape_website(base_url):
    if not base_url.startswith("http://") and not base_url.startswith("https://"):
        base_url = "https://" + base_url
    print(f"Scraping from: {base_url}")

    html = fetch_html(base_url)
    internal_links = extract_links(base_url, html)

    all_data = []

    for link in internal_links:
        article_data = extract_article(link)
        if article_data and len(article_data["content"]) > 200:
            all_data.append({
                "url": link,
                "page_type": identify_page_type(link),
                "title": article_data["title"],
                "content": article_data["content"],
                "date_published": article_data["date_published"]
            })
    print("scraping done")
    return all_data
