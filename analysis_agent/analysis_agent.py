from openai import OpenAI
import json
import os


client_openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def analyze_stock(ticker: str, stock_data: list):
    if not stock_data:
        return {"notify": False, "message": "No recent data available"}

    combined_text = "\n\n".join(
        [
            f"[{d.get('timestamp', 'no_timestamp')}] {d.get('title', '')}\n{d.get('body', '')}"
            for d in stock_data
        ]
    )

    prompt = f"""
    You are a financial analysis assistant. You receive recent information about a stock and must decide if the owner should be notified.

    Data for {ticker}:
    {combined_text}

    Analyze sentiment, risk, and market relevance.
    Respond ONLY in JSON format:
    {{
      "notify": true/false,
      "message": "short, clear reason"
    }}
    """

    response = client_openai.chat.completions.create(
        model="gpt-5",
        messages=[
            {"role": "system", "content": "You analyze financial data objectively."},
            {"role": "user", "content": prompt}
        ]
    )

    raw = response.choices[0].message.content.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"notify": False, "message": "Invalid output format."}
