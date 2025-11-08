# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import os

from analysis_agent.analysis_agent import analyze_stock
from analysis_agent.get_weaviate_data import get_data
from analysis_agent.email_sender import send_message

app = Flask(__name__)
CORS(app)  # Allow requests from your Lovable frontend

@app.route('/api/analyze', methods=['POST'])
def analyze():
    data = request.json
    ticker = data.get('ticker')
    
    # Get your environment variables
    weaviate_url = os.getenv("WEAVIATE_URL")
    weaviate_api_key = os.getenv("WEAVIATE_API_KEY")
    
    # Handle None case
    stock_data = get_data(ticker, weaviate_url, weaviate_api_key)
    
    if stock_data is None:
        # Ticker not found in database
        return jsonify({
            "action_needed": False,
            "message": f"No data available for {ticker}. This ticker may not be in the database yet."
        }), 200
    
    # Continue with analysis if data exists
    result = analyze_stock(ticker, stock_data)
    
    return jsonify(result)


@app.route('/api/send-email', methods=['POST'])
def send_email():
    data = request.json
    email = data.get('email')
    message = data.get('message')
    subject = data.get('subject')
    
    password = os.getenv("SMTP_PASSWORD")
    send_message(email, message, password, subject=subject)
    
    return jsonify({"success": True})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
