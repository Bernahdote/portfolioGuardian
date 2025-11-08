# Web Crawler AI - Intelligent Research Assistant

An AI-powered web crawler that autonomously researches topics by navigating websites, following links, and extracting relevant information.

## 🎯 What It Does

Give it a **topic**, a **goal**, and some **sources** - and it will:
- 🔍 Crawl through websites looking for relevant information
- 🔗 Intelligently follow links related to your topic
- 📄 Extract articles and content
- 💭 Record insights and observations
- 📊 Generate summaries of each page visited

## 🚀 Quick Start

### Direct CLI Usage

```bash
node stock-guardian.js \
  "AAPL" \
  "Monitor Apple stock for investment risks and opportunities" \
  '["https://news.ycombinator.com", "https://finance.yahoo.com"]' \
  '{"maxStepsPerSource": 15}'
```

### Using the API Server

```bash
# Start the server
python server.py

# Submit a research job
curl -X POST http://localhost:5000/crawl \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "AAPL",
    "goal": "Find recent news about Apple stock performance",
    "sources": ["https://news.ycombinator.com"],
    "metadata": {"maxStepsPerSource": 10}
  }'
```

### Using the Launcher (Multiple Jobs)

```bash
# Research multiple stocks in parallel
python crawler-launcher.py stocks

# Research tech topics
python crawler-launcher.py tech

# Custom research job
python crawler-launcher.py custom \
  "Climate Change" \
  "Research latest climate change news and findings" \
  https://news.ycombinator.com \
  https://techcrunch.com
```

## 📋 Parameters

### Required:
- **topic**: The subject you want to research (e.g., "AAPL", "AI Safety", "Climate Change")
- **goal**: Plain text description of what you want to achieve
- **sources**: Array of URLs to start crawling from

### Optional (metadata):
- **maxStepsPerSource**: Maximum steps per source (default: 20)
- **openaiApiKey**: Your OpenAI API key (or use env var)

## 🎨 Use Cases

### Stock Research
```bash
Topic: "TSLA"
Goal: "Monitor Tesla stock for investment risks and opportunities"
Sources: ["https://finance.yahoo.com", "https://www.cnbc.com/stocks/"]
```

### Technology Research
```bash
Topic: "AI Safety"
Goal: "Research recent developments in AI safety and alignment"
Sources: ["https://news.ycombinator.com", "https://arxiv.org"]
```

### Market Research
```bash
Topic: "Electric Vehicles"
Goal: "Understand the competitive landscape in the EV market"
Sources: ["https://techcrunch.com", "https://www.theverge.com"]
```

### News Monitoring
```bash
Topic: "Cybersecurity"
Goal: "Find recent security breaches and vulnerabilities"
Sources: ["https://news.ycombinator.com", "https://arstechnica.com"]
```

## 📂 Output Structure

Each research session creates a timestamped folder:
```
sessions/
  └── <topic>_<date>_<time>_<id>/
      ├── articles/
      │   ├── source1_step1.json    # Page summaries with links
      │   ├── source1_step2.json
      │   └── article_<hash>.json   # Extracted articles
      ├── current_thoughts.txt       # AI's recorded insights
      ├── session.json              # Full session log
      └── source1_step1.png         # Screenshots
```

### Article JSON Format
```json
{
  "step": 1,
  "url": "https://...",
  "title": "Page title",
  "aiSummary": "AI-generated summary of the page content...",
  "allLinks": [
    {"text": "Link text", "href": "https://..."}
  ],
  "pageContext": {
    "title": "...",
    "bodyPreview": "...",
    "articles": [...],
    "links": [...]
  }
}
```

## 🧠 How It Works

The crawler uses a **crawler-first approach**:

1. **Start**: Navigates to provided sources
2. **Analyze**: AI examines page content and available links
3. **Navigate**: Follows links related to the topic/goal
4. **Extract**: When landing on relevant articles, extracts full content
5. **Record**: Saves insights, summaries, and observations
6. **Repeat**: Continues until goal is achieved or max steps reached

The AI is specifically prompted to:
- ✅ NAVIGATE to follow links (primary action)
- ✅ EXTRACT_ARTICLE when finding relevant content
- ✅ RECORD_THOUGHT to capture insights
- ⚠️ Only use SEARCH/CLICK/SCROLL as fallback

## 🔧 Configuration

Set environment variables:
```bash
export OPENAI_API_KEY="your-key-here"
export LPD_TOKEN="your-lightpanda-token"
```

Or pass in metadata:
```json
{
  "openaiApiKey": "sk-...",
  "maxStepsPerSource": 20
}
```

## 📊 Three Ways to Use It

### 1. **CLI** - Direct execution
Best for: One-off research jobs
```bash
node stock-guardian.js <topic> <goal> <sources_json> <metadata_json>
```

### 2. **API Server** - HTTP endpoints
Best for: Integration with other services
```bash
python server.py
# POST /crawl - Start job
# GET /jobs/<id> - Check status
```

### 3. **Launcher** - Multiple parallel jobs
Best for: Researching multiple topics at once
```bash
python crawler-launcher.py stocks  # Run predefined jobs
```

## 🎯 Example: Stock Research Flow

```python
from crawler_launcher import CrawlerLauncher

launcher = CrawlerLauncher()

launcher.add_job(
    topic="AAPL",
    goal="Monitor Apple stock for investment risks and opportunities",
    sources=["https://finance.yahoo.com", "https://news.ycombinator.com"],
    metadata={"maxStepsPerSource": 15}
)

results = launcher.run_all_sequential()

for result in results:
    if result['success']:
        data = json.loads(result['stdout'])
        print(f"Articles: {data['articlesCollected']}")
        print(f"Insights: {data['thoughtsRecorded']}")
```

## 📝 Notes

- Only saves page data when URL changes (avoids duplicates)
- Generates AI summaries for each unique page visited
- Extracts all links (up to 100) for the AI to choose from
- Automatically follows relevant links in crawler mode
- Falls back to search/interaction only when necessary

## 🔗 See Also

- [API_README.md](./API_README.md) - Full API documentation
- [server.py](./server.py) - Flask API server
- [crawler-launcher.py](./crawler-launcher.py) - Batch launcher
- [stock-guardian.js](./stock-guardian.js) - Core crawler script
