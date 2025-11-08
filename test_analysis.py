from analysis_agent import analyze_stock
from mock_individual_stock_data import mock_weaviate_stock_data


if __name__ == "__main__":
    data = mock_weaviate_stock_data("AAPL")
    result = analyze_stock("AAPL", data)
    print(result)
