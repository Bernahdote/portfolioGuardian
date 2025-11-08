# Database Testing Guide

## Test if Database Connection Works

Run the test script to verify Weaviate connection and insertion:

```bash
uv run python test_db_insert.py
```

Or if you have weaviate-client installed globally:
```bash
python3 test_db_insert.py
```

**Expected output:**
```
Testing Weaviate connection...
URL: v0721jeoraum1hsqk0lcwq.c0.europe-west3.gcp.weaviate.cloud
API Key: WEx4cFlBd2tGUUt3d2RC...

1. Connecting to Weaviate...
   ✅ Connected successfully!

2. Getting 'News' collection...
   ✅ Collection retrieved!

3. Inserting test entry...
   Data: {'ticker': 'TEST_143522', 'signal': 'Neutral', ...}
   ✅ Inserted successfully! UUID: abc123...

4. Querying to verify insertion...
   ✅ Latest entry found:
      Ticker: TEST_143522
      Signal: Neutral
      Title: Test database insertion from crawler
      Time: 2025-11-08

============================================================
✅ ALL TESTS PASSED! Database is working correctly.
============================================================
```

## Manually Insert Saved Entries

If the crawler saved JSON files but didn't insert them, you can manually insert them:

```bash
# Insert a specific file
python3 insert_saved_entries.py sessions/AAPL_*/articles/db_entry_source1_step1.json

# Insert multiple files
python3 insert_saved_entries.py sessions/AAPL_*/articles/db_entry_*.json

# Insert all db entries from a session
python3 insert_saved_entries.py sessions/Rust_ecosystem_growth_2025-11-08_15_35_22_e876ro/articles/db_entry_*.json
```

**Example output:**
```
============================================================
Inserting: sessions/Rust_ecosystem_growth_2025-11-08_15_35_22_e876ro/articles/db_entry_source1_step1.json
============================================================

Entry data:
  Ticker: Rust ecosystem growth
  Signal: Positive
  Title: Trending Rust Projects Indicate Ecosystem Growth
  Time: 2025-11-08
  Body: The GitHub trending page for Rust showcases a variety...

Connecting to Weaviate...
Inserting to database...
✅ Successfully inserted! UUID: def456...

============================================================
Summary:
  ✅ Successful: 1
  ❌ Failed: 0
============================================================
```

## Common Issues

### 1. "No module named 'weaviate'"

Install the Weaviate client:
```bash
pip install weaviate-client
# or with uv
uv pip install weaviate-client
```

### 2. Connection timeout

Check your internet connection and verify the Weaviate URL is correct in `.env`:
```bash
WEAVIATE_URL=v0721jeoraum1hsqk0lcwq.c0.europe-west3.gcp.weaviate.cloud
```

### 3. Authentication failed

Verify your API key in `.env`:
```bash
WEAVIATE_API_KEY=WEx4cFlBd2tGUUt3d2RCRV9JUFJNQXJxdS85MldDS2t1TmNBbVB1L2NFOW9UT25tRVh1MU9LS2V2dnpZPV92MjAw
```

### 4. Collection 'News' not found

Create the News collection in Weaviate with this schema:
- `ticker` (text)
- `signal` (text)
- `title` (text)
- `body` (text)
- `time` (text/date)

## Verify Entries in Weaviate

Query your Weaviate instance to see all entries:

```python
import weaviate
from weaviate.classes.init import Auth

client = weaviate.connect_to_weaviate_cloud(
    cluster_url="v0721jeoraum1hsqk0lcwq.c0.europe-west3.gcp.weaviate.cloud",
    auth_credentials=Auth.api_key("YOUR_API_KEY"),
)

news = client.collections.get("News")

# Get all entries
results = news.query.fetch_objects(limit=10)

for item in results.objects:
    print(f"Ticker: {item.properties['ticker']}")
    print(f"Signal: {item.properties['signal']}")
    print(f"Title: {item.properties['title']}")
    print(f"Time: {item.properties['time']}")
    print()

client.close()
```

## Debug Mode

To see detailed error messages during crawler execution, the updated code now prints:
- ✅ Database insert successful messages
- ⚠️ Warning messages with full stderr/stdout on failure
- 📊 DB Entry preview before insertion

Look for these in your crawler output to diagnose issues.
