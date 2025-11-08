import json
import os
import requests
from dotenv import load_dotenv


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

