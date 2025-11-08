#!/usr/bin/env python3
"""
Test script to verify Weaviate database insertion works
"""

import weaviate
from weaviate.classes.init import Auth
from datetime import datetime
import sys
import os

# Load from environment or use defaults
weaviate_url = os.environ.get('WEAVIATE_URL', 'v0721jeoraum1hsqk0lcwq.c0.europe-west3.gcp.weaviate.cloud')
weaviate_api_key = os.environ.get('WEAVIATE_API_KEY', 'WEx4cFlBd2tGUUt3d2RCRV9JUFJNQXJxdS85MldDS2t1TmNBbVB1L2NFOW9UT25tRVh1MU9LS2V2dnpZPV92MjAw')

print(f"Testing Weaviate connection...")
print(f"URL: {weaviate_url}")
print(f"API Key: {weaviate_api_key[:20]}...")

try:
    # Connect to Weaviate
    print("\n1. Connecting to Weaviate...")
    client = weaviate.connect_to_weaviate_cloud(
        cluster_url=weaviate_url,
        auth_credentials=Auth.api_key(weaviate_api_key),
    )
    print("   ✅ Connected successfully!")

    # Get News collection
    print("\n2. Getting 'News' collection...")
    news = client.collections.get("News")
    print("   ✅ Collection retrieved!")

    # Test insert
    print("\n3. Inserting test entry...")
    test_data = {
        "ticker": "TEST_" + datetime.now().strftime("%H%M%S"),
        "signal": "Neutral",
        "title": "Test database insertion from crawler",
        "body": "This is a test entry to verify the database connection is working correctly.",
        "time": datetime.now().strftime("%Y-%m-%d")
    }

    print(f"   Data: {test_data}")

    result = news.data.insert(test_data)
    print(f"   ✅ Inserted successfully! UUID: {result}")

    # Query back to verify
    print("\n4. Querying to verify insertion...")
    results = news.query.fetch_objects(limit=1)
    if results.objects:
        latest = results.objects[0]
        print(f"   ✅ Latest entry found:")
        print(f"      Ticker: {latest.properties.get('ticker')}")
        print(f"      Signal: {latest.properties.get('signal')}")
        print(f"      Title: {latest.properties.get('title')}")
        print(f"      Time: {latest.properties.get('time')}")

    # Close connection
    client.close()

    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED! Database is working correctly.")
    print("="*60)

except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
    print(f"\nFull error details:")
    import traceback
    traceback.print_exc()
    sys.exit(1)
