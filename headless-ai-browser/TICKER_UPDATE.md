# Ticker Parameter Added

The system now accepts a separate `ticker` parameter in addition to `topic` and `goal`.

## What Changed

### Parameters (in order):
1. **ticker** - Stock symbol or identifier (e.g., "AAPL", "TSLA") - Used for database insertion
2. **topic** - Research subject (e.g., "Apple Inc", "Tesla Motors") - Used for AI reasoning
3. **goal** - Research objective (what you want to achieve)
4. **sources** - URLs to crawl

### Why?
- **ticker**: Stored in database for standardized lookup (e.g., all "AAPL" entries)
- **topic**: Used by AI to understand what to research (more descriptive than ticker)

## Usage Examples

### 1. CLI Direct

```bash
node stock-guardian.js \
  "AAPL" \
  "Apple Inc" \
  "Monitor Apple stock for investment risks" \
  '["https://news.ycombinator.com"]' \
  '{"maxStepsPerSource":15}'
```

### 2. Flask API

```bash
curl -X POST http://localhost:5000/crawl \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "AAPL",
    "topic": "Apple Inc",
    "goal": "Monitor Apple stock for investment risks and opportunities",
    "sources": ["https://news.ycombinator.com"],
    "metadata": {"maxStepsPerSource": 15}
  }'
```

### 3. Python Launcher

```python
from stock_launcher import StockLauncher

launcher = StockLauncher()

launcher.add_job(
    ticker="AAPL",
    topic="Apple Inc",
    goal="Monitor Apple stock for investment risks",
    sources=["https://news.ycombinator.com"],
    metadata={"maxStepsPerSource": 15}
)

results = launcher.run_all_parallel()
```

**Or CLI:**
```bash
python stock-launcher.py custom "AAPL" "Apple Inc" "Monitor Apple stock" https://news.ycombinator.com
```

## Database Entry Format

Now includes both ticker and topic:

```json
{
  "ticker": "AAPL",          // Used for database queries
  "topic": "Apple Inc",      // Descriptive name for reference
  "signal": "Positive",
  "title": "Apple announces strong Q4 earnings",
  "body": "...",
  "time": "2025-11-08",
  "metadata": {
    "step": 1,
    "source": "https://...",
    "url": "https://...",
    "timestamp": "2025-11-08T15:00:00Z"
  }
}
```

## Migration from Old Format

**Old format (3 args):**
```bash
node stock-guardian.js "AAPL" "Monitor Apple stock" '["https://..."]'
```

**New format (4 args):**
```bash
node stock-guardian.js "AAPL" "Apple Inc" "Monitor Apple stock" '["https://..."]'
```

## Benefits

1. **Database consistency**: All entries for a stock use the same ticker (AAPL)
2. **Better AI reasoning**: Topic can be more descriptive ("Apple Inc" vs "AAPL")
3. **Flexible topics**: ticker="TECH", topic="Technology sector trends"
4. **Clear separation**: ticker for storage/lookup, topic for research context

## Files Updated

- ✅ `stock-guardian.js` - Core crawler
- ✅ `server.py` - Flask API server
- ✅ `stock-launcher.py` - Python batch launcher
- ✅ Database entry JSON format
- ✅ Session logs and output
