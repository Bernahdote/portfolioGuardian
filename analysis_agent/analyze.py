import os

from analysis_agent import analyze_stock
from get_weaviate_data import get_data
from email_sender import send_message


if __name__ == "__main__":
    customer_mail = "bergkvist.teo@protonmail.com"

    password = os.getenv("SMTP_PASSWORD")

    weaviate_url = os.getenv("WEAVIATE_URL")
    weaviate_api_key = os.getenv("WEAVIATE_API_KEY")

    data = get_data("AAPL", weaviate_url, weaviate_api_key)
    result = analyze_stock("AAPL", data)
    print(result)
    send_message(customer_mail, result["message"], password)
