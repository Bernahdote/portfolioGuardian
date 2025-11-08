import json
import os
import requests
from dotenv import load_dotenv
from newspaper import Article
import time
from expand_tickers import process_news_articles


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
                
            # Remove similar articles - we don't want them
            if "similar" in article:
                del article["similar"]
    
    # Process tickers: check if articles have tickers and expand them with OpenAI
    print("\nProcessing tickers and expanding with OpenAI...")
    articles_data = process_news_articles(articles_data)
    
    output_file = "news_articles.json"
    
    # Load existing articles if file exists
    existing_uuids = set()
    existing_data = {"meta": {}, "data": []}
    
    if os.path.exists(output_file):
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
                if isinstance(existing_data, dict) and "data" in existing_data:
                    existing_uuids = {article.get("uuid") for article in existing_data["data"] if article.get("uuid")}
                    print(f"Found {len(existing_uuids)} existing articles")
        except (json.JSONDecodeError, Exception) as e:
            print(f"Warning: Could not read existing file: {e}. Starting fresh.")
            existing_data = {"meta": {}, "data": []}
    
    # Filter out articles that already exist (by UUID)
    if isinstance(articles_data, dict) and "data" in articles_data:
        new_articles = [article for article in articles_data["data"] if article.get("uuid") not in existing_uuids]
        existing_articles = existing_data.get("data", [])
        
        print(f"New articles to add: {len(new_articles)}")
        print(f"Existing articles: {len(existing_articles)}")
        
        # Combine existing and new articles
        combined_data = {
            "meta": articles_data.get("meta", existing_data.get("meta", {})),
            "data": existing_articles + new_articles
        }
        
        # Write combined data
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(combined_data, f, indent=2, ensure_ascii=False, default=str)
        
        total_count = len(combined_data["data"])
        print(f"Total articles in file: {total_count}")
    else:
        # Fallback: just write the new data if structure is unexpected
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(articles_data, f, indent=2, ensure_ascii=False, default=str)
        print("Wrote articles to file (unexpected data structure)")


if __name__ == "__main__":
    main()

