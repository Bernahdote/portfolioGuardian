import json
import os
import requests
from dotenv import load_dotenv
from newspaper import Article
import time


def scrape_article_text(url):
    """
    Scrape the full text content from an article URL.
    Returns the full text or None if scraping fails.
    """
    try:
        article = Article(url)
        article.download()
        article.parse()
        return article.text
    except Exception as e:
        print(f"Error scraping {url}: {str(e)}")
        return None


def main():
    load_dotenv()
    
    api_key = os.getenv("NEWS_API_KEY")
    
    if not api_key:
        raise ValueError("NEWS_API_KEY not found in .env file")
    
    url = "https://api.marketaux.com/v1/news/all"
    params = {

        "api_token": api_key
    }
    
    response = requests.get(url, params=params)
    response.raise_for_status()
    
    articles_data = response.json()
    
    if isinstance(articles_data, dict) and "data" in articles_data:
        articles = articles_data["data"]
        print(f"Scraping full text for {len(articles)} articles...")
        
        for i, article in enumerate(articles, 1):
            if "url" in article:
                print(f"Scraping article {i}/{len(articles)}: {article.get('title', 'Unknown')[:50]}...")
                full_text = scrape_article_text(article["url"])
                article["full_text"] = full_text
                
        
        for article in articles:
            if "similar" in article and isinstance(article["similar"], list):
                for similar_article in article["similar"]:
                    if "url" in similar_article and "full_text" not in similar_article:
                        print(f"Scraping similar article: {similar_article.get('title', 'Unknown')[:50]}...")
                        full_text = scrape_article_text(similar_article["url"])
                        similar_article["full_text"] = full_text
                        time.sleep(0.5)
    
    output_file = "news_articles.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(articles_data, f, indent=2, ensure_ascii=False, default=str)
    
    if isinstance(articles_data, dict) and "data" in articles_data:
        article_count = len(articles_data["data"])
    elif isinstance(articles_data, list):
        article_count = len(articles_data)
    else:
        article_count = "N/A"
    
    print(f"Number of articles: {article_count}")


if __name__ == "__main__":
    main()

