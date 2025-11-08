# Database Integration

The crawler now automatically stores research findings to a Weaviate database after each step where the URL changes.

## How It Works

After each navigation step, the system:

1. **Generates an AI Summary** of the page content
2. **Creates a Database Entry** with:
   - `ticker`: The research topic (e.g., "AAPL", "Climate Change")
   - `signal`: "Positive", "Negative", or "Neutral" sentiment
   - `title`: A concise headline (max 10 words)
   - `body`: Detailed summary including explored links
   - `time`: Current date (YYYY-MM-DD)

3. **Inserts to Weaviate** News collection

## Configuration

### Environment Variables

Add to your `.env` file:

```bash
# Optional - database integration
WEAVIATE_URL=your-cluster-url.weaviate.cloud
WEAVIATE_API_KEY=your-api-key
```

### Metadata

Or pass in metadata when running:

```bash
node stock-guardian.js \
  "AAPL" \
  "Monitor Apple stock" \
  '["https://news.ycombinator.com"]' \
  '{
    "maxStepsPerSource": 15,
    "weaviateUrl": "your-url.weaviate.cloud",
    "weaviateApiKey": "your-key"
  }'
```

### Via API

```bash
curl -X POST http://localhost:5000/crawl \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "AAPL",
    "goal": "Monitor Apple stock for risks",
    "sources": ["https://news.ycombinator.com"],
    "metadata": {
      "weaviateUrl": "your-url.weaviate.cloud",
      "weaviateApiKey": "your-key"
    }
  }'
```

## Database Schema

The data is inserted into the `News` collection with this structure:

```json
{
  "ticker": "AAPL",
  "signal": "Positive",
  "title": "Apple announces strong Q4 earnings",
  "body": "Apple reported quarterly earnings that exceeded analyst expectations, driven by strong iPhone sales. The company explored partnerships in the AI space. Key sources reviewed include TechCrunch analysis and Bloomberg reports.",
  "time": "2025-11-08"
}
```

## Signal Classification

The AI determines the signal based on:

- **Positive**: Good news, opportunities, growth, favorable developments
- **Negative**: Risks, challenges, losses, unfavorable developments
- **Neutral**: Informational, balanced, or unclear impact

## Example Output

During crawling, you'll see:

```
🔄 URL changed from initial to https://news.ycombinator.com
🤖 Generating AI summary...
💾 Saved context to: source1_step1.json
📝 Summary: The page displays recent tech news including discussions about...
🔗 Found 85 links
🗄️  Generating database entry...
📊 DB Entry - Signal: Positive, Title: Tech news highlights Apple innovation
✅ Database insert successful
```

## Disabling Database Integration

If you don't set `WEAVIATE_URL` and `WEAVIATE_API_KEY`, the database integration is automatically disabled and the crawler works normally without it.

## Querying the Data

You can query the stored data from your Weaviate instance:

```python
import weaviate
from weaviate.classes.init import Auth

client = weaviate.connect_to_weaviate_cloud(
    cluster_url="your-url.weaviate.cloud",
    auth_credentials=Auth.api_key("your-key"),
)

news = client.collections.get("News")

# Query by ticker
results = news.query.fetch_objects(
    filters={"path": ["ticker"], "operator": "Equal", "valueText": "AAPL"},
    limit=10
)

for item in results.objects:
    print(f"{item.properties['signal']} - {item.properties['title']}")
    print(f"  {item.properties['body']}")
```

## Benefits

- **Structured storage** of all research findings
- **Semantic search** capabilities via Weaviate
- **Signal tracking** for sentiment analysis
- **Link provenance** - body includes explored links
- **Time-series data** for trend analysis
