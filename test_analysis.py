import os

from analysis_agent import analyze_stock
from mock_individual_stock_data import mock_weaviate_stock_data
from email_sender import send_message


if __name__ == "__main__":
    customer_mail = "bergkvist.teo@protonmail.com"
    password = os.getenv("SMTP_PASSWORD")

    data = mock_weaviate_stock_data("AAPL")
    result = analyze_stock("AAPL", data)
    print(result)
    send_message(customer_mail, result, password)
