def mock_weaviate_stock_data(ticker: str):
    """
    Simulated stock data response to use until the real Weaviate integration is ready.
    Structure matches what get_recent_stock_data() would return.
    """
    return [
        {
            "text": f"{ticker} CEO announces a new strategic partnership with a major AI company.",
            "sentiment": 0.82,
            "timestamp": "2025-11-07T13:00:00Z",
        },
        {
            "text": f"Analysts express concern over {ticker}'s declining profit margins in the latest earnings report.",
            "sentiment": -0.45,
            "timestamp": "2025-11-06T08:00:00Z",
        },
        {
            "text": f"{ticker} stock price surges after positive quarterly results beat expectations.",
            "sentiment": 0.91,
            "timestamp": "2025-11-05T15:30:00Z",
        },
        {
            "text": f"Rumors suggest upcoming layoffs at {ticker} to cut operational costs.",
            "sentiment": -0.61,
            "timestamp": "2025-11-04T11:00:00Z",
        }
    ]
