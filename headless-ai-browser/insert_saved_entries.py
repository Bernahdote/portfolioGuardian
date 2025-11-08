#!/usr/bin/env python3
"""
Manually insert saved db_entry JSON files to Weaviate
Usage: python insert_saved_entries.py sessions/AAPL_2025-11-08.../articles/db_entry_source1_step1.json
"""

import weaviate
from weaviate.classes.init import Auth
import json
import sys
import os

# Load from environment or use defaults
weaviate_url = os.environ.get('WEAVIATE_URL', 'v0721jeoraum1hsqk0lcwq.c0.europe-west3.gcp.weaviate.cloud')
weaviate_api_key = os.environ.get('WEAVIATE_API_KEY', 'WEx4cFlBd2tGUUt3d2RCRV9JUFJNQXJxdS85MldDS2t1TmNBbVB1L2NFOW9UT25tRVh1MU9LS2V2dnpZPV92MjAw')

def insert_entry(filepath):
    """Insert a saved db_entry JSON file to Weaviate"""

    print(f"\n{'='*60}")
    print(f"Inserting: {filepath}")
    print(f"{'='*60}")

    # Read the JSON file
    with open(filepath, 'r') as f:
        data = json.load(f)

    print(f"\nEntry data:")
    print(f"  Ticker: {data['ticker']}")
    print(f"  Signal: {data['signal']}")
    print(f"  Title: {data['title']}")
    print(f"  Time: {data['time']}")
    print(f"  Body: {data['body'][:100]}...")

    try:
        # Connect to Weaviate
        print(f"\nConnecting to Weaviate...")
        client = weaviate.connect_to_weaviate_cloud(
            cluster_url=weaviate_url,
            auth_credentials=Auth.api_key(weaviate_api_key),
        )

        # Get News collection
        news = client.collections.get("News")

        # Insert the entry
        print(f"Inserting to database...")
        result = news.data.insert({
            "ticker": data['ticker'],
            "signal": data['signal'],
            "title": data['title'],
            "body": data['body'],
            "time": data['time']
        })

        print(f"✅ Successfully inserted! UUID: {result}")

        client.close()
        return True

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python insert_saved_entries.py <path_to_db_entry.json> [<path2> ...]")
        print("\nExample:")
        print("  python insert_saved_entries.py sessions/AAPL_*/articles/db_entry_*.json")
        sys.exit(1)

    filepaths = sys.argv[1:]

    print(f"\nWeaviate URL: {weaviate_url}")
    print(f"API Key: {weaviate_api_key[:20]}...")

    success_count = 0
    fail_count = 0

    for filepath in filepaths:
        if insert_entry(filepath):
            success_count += 1
        else:
            fail_count += 1

    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  ✅ Successful: {success_count}")
    print(f"  ❌ Failed: {fail_count}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
