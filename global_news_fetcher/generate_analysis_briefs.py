import json
import os
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv
from openai import OpenAI


def load_articles(file_path: str) -> Dict[str, Any]:
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def ensure_client() -> OpenAI:
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment or .env file")
    return OpenAI(api_key=api_key)


def build_prompt(article: Dict[str, Any], ticker: str, impact_data: Dict[str, Any]) -> str:
    title = article.get("title", "Unknown title")
    description = article.get("description", "")
    summary = article.get("ticker_info", {}).get("summary") or ""
    full_text = article.get("full_text", "")[:1200]
    impact = impact_data.get("impact", "unknown")
    explanation = impact_data.get("explanation", "No prior analysis available.")

    return f"""
You are preparing research hand-offs for another financial analysis agent.
Using the provided article context and ticker-specific impact notes, craft a tightly scoped research brief.

Article Title: {title}
Article Description: {description}
Article Summary: {summary}
Article Excerpt: {full_text}

Target Ticker: {ticker}

Return ONLY valid JSON in this exact shape (no markdown):
{{
  "ticker": "{ticker}",
  "topic": "Short headline-style topic (<=15 words) that captures the angle another agent should explore.",
  "goal": "One actionable objective describing what the agent must determine about the ticker's exposure.",
  "resources": [
    {{
      "title": "Name of a reputable website, news source, or data provider",
      "url": "https://example.com",
      "why": "Brief reason this source helps evaluate the impact"
    }}
  ]
}}

Guidelines:
- Base the topic and goal on the news narrative.
- Provide 2-3 unique, high-quality base domain URLs only (e.g., https://example.com, NOT https://example.com/specific/article/path).
- URLs must be ONLY the base domain with https:// prefix - no paths, no query parameters, no fragments.
- The analysis agent will browse these websites themselves to find relevant information, so provide only the domain name.
- Focus on reputable sources (financial news sites, company investor relations pages, regulatory filing sites, industry data providers). Avoid blogs and duplicate domains whenever possible.
- If strong sources are unavailable, surface the closest credible base domains and explain the gap in the `why` field.
"""


def normalize_url_to_base(url: str) -> str:
    """
    Normalize a URL to its base domain only (e.g., https://example.com).
    Removes paths, query parameters, and fragments.
    """
    if not url:
        return url
    
    # Ensure URL has a scheme
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    
    try:
        parsed = urlparse(url)
        # Reconstruct base URL with scheme and netloc only
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        return base_url
    except Exception:
        # If parsing fails, return as-is (shouldn't happen with valid URLs)
        return url


def normalize_brief_urls(brief: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize all URLs in the brief's resources to base domains only.
    """
    if "resources" in brief and isinstance(brief["resources"], list):
        for resource in brief["resources"]:
            if "url" in resource and isinstance(resource["url"], str):
                resource["url"] = normalize_url_to_base(resource["url"])
    return brief


def parse_response(raw_response: str) -> Dict[str, Any]:
    content = raw_response.strip()
    if content.startswith("```"):
        lines = content.split("\n")
        content = "\n".join(lines[1:-1]) if len(lines) > 2 else content
    parsed = json.loads(content)
    # Normalize URLs to base domains
    return normalize_brief_urls(parsed)


def generate_brief(
    client: OpenAI, article: Dict[str, Any], ticker: str, impact_data: Dict[str, Any]
) -> Dict[str, Any]:
    prompt = build_prompt(article, ticker, impact_data)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You create concise research briefs for financial analysis agents. Respond with valid JSON only.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        max_tokens=800,
    )

    raw_response = response.choices[0].message.content or ""
    return parse_response(raw_response)


def build_crawl_payload(article: Dict[str, Any], ticker: str, brief: Dict[str, Any]) -> Dict[str, Any]:
    resources = brief.get("resources") or []
    sources = [
        resource.get("url")
        for resource in resources
        if isinstance(resource, dict) and resource.get("url")
    ]

    if not sources and article.get("url"):
        sources.append(normalize_url_to_base(article["url"]))

    metadata = {
        "article_uuid": article.get("uuid"),
        "article_title": article.get("title"),
        "published_at": article.get("published_at"),
        "maxStepsPerSource": 10,
    }
    metadata = {k: v for k, v in metadata.items() if v is not None}

    return {
        "ticker": ticker,
        "topic": brief.get("topic", ""),
        "goal": brief.get("goal", ""),
        "sources": sources,
        "metadata": metadata,
    }


def dispatch_brief_to_crawler(
    payload: Dict[str, Any],
    endpoint: Optional[str] = None,
    print_output: bool = True,
) -> None:
    crawler_endpoint = endpoint or os.getenv("CRAWLER_ENDPOINT", "http://localhost:5050/crawl")
    try:
        response = requests.post(crawler_endpoint, json=payload, timeout=30)
        if print_output:
            if response.ok:
                print(f"  Crawl job dispatched (status {response.status_code}).")
            else:
                print(f"  Crawl job failed with status {response.status_code}: {response.text[:200]}")
    except requests.RequestException as exc:
        if print_output:
            print(f"  Failed to send crawl job: {exc}")


def generate_briefs_for_articles(
    articles: List[Dict[str, Any]],
    client: Optional[OpenAI] = None,
    print_output: bool = True,
) -> List[Dict[str, Any]]:
    """Generate analysis briefs for every ticker in the provided articles."""
    if not articles:
        if print_output:
            print("No articles supplied for brief generation.")
        return []

    client = client or ensure_client()
    briefs: List[Dict[str, Any]] = []

    for article in articles:
        title = article.get("title", "Unknown article")
        if article.get("analysis_briefs_generated"):
            if print_output:
                print(f"\nArticle: {title}")
                print("  Skipping brief generation (already completed).")
            continue

        ticker_info = article.get("ticker_info", {})
        tickers: List[str] = ticker_info.get("expanded_tickers") or []
        impacts = ticker_info.get("ticker_impacts") or {}
        article_completed = False

        if not tickers:
            # Nothing to analyze; mark as done to avoid re-processing.
            article["analysis_briefs_generated"] = True
            continue

        if print_output:
            print(f"\nArticle: {title}")

        for ticker in tickers:
            impact_data = impacts.get(
                ticker,
                {
                    "impact": "neutral",
                    "explanation": "No impact details returned from the ticker expansion step.",
                },
            )

            try:
                brief = generate_brief(client, article, ticker, impact_data)
                brief_entry = {
                    "article_uuid": article.get("uuid"),
                    "title": title,
                    "ticker": ticker,
                    "brief": brief,
                }
                briefs.append(brief_entry)

                payload = build_crawl_payload(article, ticker, brief)
                if print_output:
                    print(f"Ticker {ticker}: dispatching crawl job...")
                dispatch_brief_to_crawler(payload, print_output=print_output)
                article_completed = True
            except json.JSONDecodeError as exc:
                if print_output:
                    print(f"  Failed to parse response for {ticker}: {exc}")
            except Exception as exc:
                if print_output:
                    print(f"  Error while generating brief for {ticker}: {exc}")
        if article_completed:
            article["analysis_briefs_generated"] = True

    if print_output and not briefs:
        print("No tickers with briefs were generated.")

    return briefs


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    articles_path = os.path.join(script_dir, "news_articles.json")

    if not os.path.exists(articles_path):
        raise FileNotFoundError(f"Could not find news_articles.json at {articles_path}")

    articles_data = load_articles(articles_path)
    articles = articles_data.get("data", [])
    generate_briefs_for_articles(articles)


if __name__ == "__main__":
    main()
