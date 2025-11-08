import os
import json
from dotenv import load_dotenv
from openai import OpenAI


def get_tickers_from_article(article):
    """
    Extract ticker symbols from an article's entities field.
    Returns a list of ticker symbols (e.g., ['AAPL', 'MSFT']).
    """
    tickers = []
    if "entities" in article and isinstance(article["entities"], list):
        for entity in article["entities"]:
            if "symbol" in entity and entity["symbol"]:
                tickers.append(entity["symbol"])
    return tickers


def expand_tickers_with_openai(article, existing_tickers):
    """
    Use OpenAI to find all relevant tickers that may be affected by the news article.
    
    Args:
        article: News article dictionary with title, description, full_text, etc.
        existing_tickers: List of tickers already found in the article
    
    Returns:
        Tuple of (list of tickers, summary string, ticker_impacts dict)
        ticker_impacts: Dictionary mapping ticker -> {"impact": "positive"/"negative"/"neutral", "explanation": "..."}
    """
    load_dotenv()
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in .env file")
    
    client = OpenAI(api_key=api_key)
    
    # Prepare article content for analysis
    title = article.get("title", "")
    description = article.get("description", "")
    full_text = article.get("full_text", "")
    
    # Combine content (prefer full_text if available, otherwise use title + description)
    article_content = full_text if full_text else f"{title}\n{description}"
    
    # Limit content length to avoid token limits
    if len(article_content) > 8000:
        article_content = article_content[:8000]
    
    existing_tickers_str = ", ".join(existing_tickers) if existing_tickers else "none"
    
    prompt = f"""
You are a financial analyst. Analyze the following news article and identify ALL relevant stock tickers that may be affected by this news.

Existing tickers found in the article: {existing_tickers_str}

Article:
Title: {title}
Description: {description}
Content: {article_content[:4000]}

Based on the news content, identify:
1. The tickers already mentioned (if any)
2. Related companies in the same industry that may be affected
3. Competitors, suppliers, or customers that could be impacted
4. Companies in related sectors that might be influenced by this news

For EACH ticker, determine:
- Whether the news affects the stock POSITIVELY, NEGATIVELY, or NEUTRALLY
- A clear explanation of WHY this ticker is affected, written so that someone who has never read the news article can understand it

Return a JSON object with this exact format:
{{
  "tickers": ["AAPL", "MSFT", "GOOGL"],
  "ticker_impacts": {{
    "AAPL": {{
      "impact": "positive",
      "explanation": "Clear explanation of why AAPL is affected, written for someone who hasn't read the news"
    }},
    "MSFT": {{
      "impact": "negative",
      "explanation": "Clear explanation of why MSFT is affected, written for someone who hasn't read the news"
    }},
    "GOOGL": {{
      "impact": "neutral",
      "explanation": "Clear explanation of why GOOGL is affected, written for someone who hasn't read the news"
    }}
  }},
  "summary": "Overall summary of the news and its market implications"
}}

Important:
- "impact" must be one of: "positive", "negative", or "neutral"
- "explanation" should be clear and self-contained - explain what happened and why it affects this specific ticker
- Include ALL tickers in the "ticker_impacts" object
- Return ONLY valid JSON
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Using a more cost-effective model
            messages=[
                {"role": "system", "content": "You are a financial analyst that identifies stock tickers from news articles. Always respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1000  # Increased for detailed explanations
        )
        
        raw_response = response.choices[0].message.content.strip()
        print(raw_response)

        # Try to parse JSON response
        # Sometimes the response might be wrapped in markdown code blocks
        if raw_response.startswith("```"):
            # Remove markdown code blocks
            lines = raw_response.split("\n")
            raw_response = "\n".join(lines[1:-1]) if len(lines) > 2 else raw_response
        
        parsed_response = json.loads(raw_response)
        
        # Extract summary if available
        summary = ""
        if isinstance(parsed_response, dict) and "summary" in parsed_response:
            summary = parsed_response["summary"]
        
        # Extract ticker impacts
        ticker_impacts = {}
        if isinstance(parsed_response, dict) and "ticker_impacts" in parsed_response:
            ticker_impacts = parsed_response["ticker_impacts"]
        
        # Handle different response formats for tickers
        tickers = []
        if isinstance(parsed_response, dict):
            # If it's a dict, look for common keys that might contain tickers
            if "tickers" in parsed_response:
                tickers = parsed_response["tickers"]
            elif "ticker" in parsed_response:
                tickers = [parsed_response["ticker"]]
            elif "symbols" in parsed_response:
                tickers = parsed_response["symbols"]
            elif "ticker_impacts" in parsed_response:
                # Extract tickers from ticker_impacts keys
                tickers = list(parsed_response["ticker_impacts"].keys())
            else:
                # Try to extract string values that look like tickers
                for value in parsed_response.values():
                    if isinstance(value, list):
                        tickers.extend([v for v in value if isinstance(v, str)])
                    elif isinstance(value, str) and len(value) <= 5:
                        tickers.append(value)
        elif isinstance(parsed_response, list):
            # If it's a list, extract tickers from it
            for item in parsed_response:
                if isinstance(item, str):
                    # Direct ticker symbol
                    tickers.append(item)
                elif isinstance(item, dict):
                    # Extract ticker from dict (e.g., {"ticker": "AAPL", "reason": "..."})
                    if "ticker" in item:
                        tickers.append(item["ticker"])
                    elif "symbol" in item:
                        tickers.append(item["symbol"])
                    else:
                        # Try to find any string value that looks like a ticker
                        for key, value in item.items():
                            if isinstance(value, str) and len(value) <= 5 and value.isupper():
                                tickers.append(value)
                                break
        else:
            # If it's a single string, treat it as a ticker
            if isinstance(parsed_response, str):
                tickers = [parsed_response]
        
        # Filter to only valid ticker symbols (strings, uppercase, reasonable length)
        tickers = [t.upper().strip() for t in tickers if isinstance(t, str) and len(t.strip()) <= 5 and t.strip().isalnum()]
        
        # Remove duplicates
        tickers = list(set(tickers))
        
        # Normalize ticker_impacts keys to uppercase and validate impact values
        normalized_impacts = {}
        for ticker, impact_data in ticker_impacts.items():
            ticker_upper = ticker.upper().strip()
            if isinstance(impact_data, dict):
                impact = impact_data.get("impact", "neutral").lower()
                if impact not in ["positive", "negative", "neutral"]:
                    impact = "neutral"
                explanation = impact_data.get("explanation", "")
                normalized_impacts[ticker_upper] = {
                    "impact": impact,
                    "explanation": explanation
                }
        
        # Ensure all tickers have impact data (fill missing ones with neutral)
        for ticker in tickers:
            if ticker not in normalized_impacts:
                normalized_impacts[ticker] = {
                    "impact": "neutral",
                    "explanation": "Impact analysis not available"
                }
        
        # Return tickers, summary, and ticker impacts
        return tickers, summary, normalized_impacts
        
    except json.JSONDecodeError as e:
        print(f"Error parsing OpenAI response: {e}")
        print(f"Raw response: {raw_response}")
        # Fallback to existing tickers if parsing fails
        default_impacts = {ticker: {"impact": "neutral", "explanation": "Unable to analyze impact"} for ticker in existing_tickers}
        return existing_tickers, "", default_impacts
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        # Fallback to existing tickers if API call fails
        default_impacts = {ticker: {"impact": "neutral", "explanation": "Unable to analyze impact"} for ticker in existing_tickers}
        return existing_tickers, "", default_impacts


def process_article_tickers(article):
    """
    Process a single article to extract and expand tickers.
    
    Args:
        article: News article dictionary
    
    Returns:
        Dictionary with:
        - has_tickers: bool
        - original_tickers: list of tickers found in entities
        - expanded_tickers: list of all relevant tickers (if OpenAI was called)
    """
    # Extract existing tickers from entities
    original_tickers = get_tickers_from_article(article)
    
    result = {
        "has_tickers": len(original_tickers) > 0,
        "original_tickers": original_tickers,
        "expanded_tickers": original_tickers.copy(),  # Default to original tickers
        "summary": "",  # Summary from OpenAI
        "ticker_impacts": {}  # Dictionary of ticker -> impact info
    }
    
    # If there are tickers, expand them using OpenAI
    if True: #result["has_tickers"]:
        try:
            print(f"  Found tickers: {', '.join(original_tickers)} - Expanding with OpenAI...")
            expanded, summary, ticker_impacts = expand_tickers_with_openai(article, original_tickers)
            result["expanded_tickers"] = expanded
            result["summary"] = summary
            result["ticker_impacts"] = ticker_impacts
            if len(expanded) > len(original_tickers):
                new_tickers = set(expanded) - set(original_tickers)
                print(f"  Expanded to: {', '.join(expanded)} (added: {', '.join(new_tickers)})")
            else:
                print(f"  Expanded to: {', '.join(expanded)}")
            if summary:
                print(f"  Summary: {summary[:100]}...")
            # Print impact summary
            for ticker, impact_info in ticker_impacts.items():
                impact = impact_info.get("impact", "neutral")
                print(f"    {ticker}: {impact.upper()}")
        except Exception as e:
            print(f"  Error expanding tickers for article '{article.get('title', 'Unknown')}': {e}")
            # Keep original tickers if expansion fails
            result["expanded_tickers"] = original_tickers
            result["ticker_impacts"] = {ticker: {"impact": "neutral", "explanation": "Analysis failed"} for ticker in original_tickers}
    else:
        print(f"  No tickers found in article")
    
    return result


def process_news_articles(articles_data):
    """
    Process all articles in the news data structure.
    
    Args:
        articles_data: Dictionary with "data" key containing list of articles
    
    Returns:
        Updated articles_data with "relevant_tickers" field added to each article
    """
    if not isinstance(articles_data, dict) or "data" not in articles_data:
        return articles_data
    
    articles = articles_data["data"]
    
    for i, article in enumerate(articles, 1):
        print(f"Processing article {i}/{len(articles)}: {article.get('title', 'Unknown')[:50]}...")
        ticker_info = process_article_tickers(article)
        article["ticker_info"] = ticker_info
        
        # Remove similar articles - we don't want them
        if "similar" in article:
            del article["similar"]
    
    return articles_data

