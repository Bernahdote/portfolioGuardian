# Stock Guardian AI Agent

An intelligent AI agent that monitors stocks by scraping news sources, extracting relevant articles, and maintaining a memory of insights about your portfolio.

## Features

- **Stock-Focused Intelligence**: Specialized prompts for financial monitoring
- **Memory System**: Maintains `current_thoughts.txt` - a living document of AI insights
- **Article Storage**: Saves full article text for each URL visited
- **Multi-Source Monitoring**: Can check multiple news sites per stock
- **Sentiment Analysis**: Tracks positive/negative/neutral sentiment
- **Parallel Processing**: Monitor multiple stocks simultaneously

## Installation

```bash
npm install
```

Make sure you have your OpenAI API key set:
```bash
export OPENAI_API_KEY="your-key-here"
```

## Usage

### Quick Start - Monitor Tech Stocks

```bash
uv run stock-launcher.py tech
```

This will monitor AAPL, MSFT, and NVDA across tech news sources.

### Monitor a Single Stock

```bash
node stock-guardian.js "AAPL" '["https://news.ycombinator.com","https://techcrunch.com"]'
```

### Monitor Custom Stock with Python Launcher

```bash
uv run stock-launcher.py custom TSLA https://news.ycombinator.com https://finance.yahoo.com
```

### Python Library Usage

```python
from stock_launcher import StockGuardianLauncher

launcher = StockGuardianLauncher(base_port=9222)

# Add stocks to monitor
launcher.add_stock(
    ticker="AAPL",
    sources=[
        "https://news.ycombinator.com",
        "https://techcrunch.com"
    ],
    metadata={"maxStepsPerSource": 20}
)

launcher.add_stock(
    ticker="TSLA",
    sources=["https://finance.yahoo.com"],
    metadata={"maxStepsPerSource": 15}
)

# Run in parallel
results = launcher.run_all_parallel()

for result in results:
    print(f"{result['ticker']}: {result['success']}")
```

## How It Works

### 1. AI-Driven Navigation
The agent uses GPT-4o-mini with a specialized "Stock Guardian" system prompt that:
- Focuses on finding stock-relevant news
- Searches for the ticker symbol on each source
- Identifies and clicks on relevant articles
- Extracts full article content

### 2. Memory System - `current_thoughts.txt`
The agent maintains a running commentary of its findings:

```
Stock Guardian - Monitoring AAPL
Session: AAPL_2025-01-08_14_30_45_abc123
Started: 2025-01-08T14:30:45.123Z
============================================================

[2025-01-08T14:31:22.456Z] [NEGATIVE] [HIGH]
Apple faces supply chain disruptions in China, potentially affecting Q1 earnings.

[2025-01-08T14:32:15.789Z] [POSITIVE] [MEDIUM]
New iPhone model receives strong pre-order numbers, analyst upgrades price target.
```

### 3. Article Storage - `articles/` Directory
Each article is saved as a separate JSON file:

```json
{
  "url": "https://techcrunch.com/2025/01/08/apple-news",
  "title": "Apple Announces New Product Line",
  "content": "Full article text here...",
  "timestamp": "2025-01-08T14:31:22.456Z",
  "headings": ["Apple Announces...", "Key Features"],
  "links": [
    {"text": "Related Story", "href": "..."}
  ]
}
```

## Actions Available to the AI

The Stock Guardian AI can:

1. **TYPE**: Enter search terms (like the ticker symbol)
2. **PRESS_ENTER**: Submit search forms
3. **CLICK**: Click on links to articles
4. **NAVIGATE**: Go to specific URLs
5. **SCROLL**: Scroll to see more content
6. **EXTRACT_ARTICLE**: Save full article content
7. **RECORD_THOUGHT**: Add insights to memory
8. **DONE**: Complete monitoring for a source

## Session Output Structure

```
sessions/
└── AAPL_2025-01-08_14_30_45_abc123/
    ├── current_thoughts.txt        # AI's running commentary
    ├── session.json                # Full session log
    ├── articles/                   # Extracted articles
    │   ├── article_abc123.json
    │   ├── article_def456.json
    │   └── ...
    ├── source1_step1.png          # Screenshots
    ├── source1_step2.png
    └── ...
```

## Configuration

### Metadata Options

```javascript
{
  "port": 9222,              // Browser port (increment for parallel)
  "maxStepsPerSource": 20,   // Max AI steps per news source
  "openaiApiKey": "..."      // Optional: override env var
}
```

## Example Workflow

1. **Agent starts** monitoring AAPL on Hacker News
2. **Searches** for "AAPL" in the search box
3. **Scans results** for relevant articles
4. **Clicks** on article about Apple earnings
5. **Extracts** full article text → saves to `articles/article_xyz.json`
6. **Records thought**: "Earnings beat expectations [POSITIVE] [HIGH]"
7. **Continues** searching for more articles
8. **Moves** to next source (TechCrunch)
9. **Repeats** the process

## Best Practices

- Use 2-3 reliable news sources per stock
- Set `maxStepsPerSource` based on source complexity (15-20 is good)
- Run monitoring on a schedule (cron/scheduled task)
- Review `current_thoughts.txt` for quick insights
- Parse `articles/*.json` for detailed analysis

## Tips

- **Different ports for parallel**: Each browser instance needs its own port
- **Quality sources**: Use reputable financial news sites
- **Monitoring frequency**: Run once per day or when markets are volatile
- **Post-processing**: Build dashboards from the collected data

## Troubleshooting

- **Port conflicts**: Increment port numbers for parallel instances
- **API rate limits**: Use delays or reduce maxSteps
- **Missing articles**: Some sites may have anti-scraping measures
- **Incomplete thoughts**: Increase maxStepsPerSource to allow more exploration

## Future Enhancements

- [ ] Add Claude vision support for better page understanding
- [ ] Implement sentiment scoring algorithms
- [ ] Create summary reports across multiple sessions
- [ ] Add alerts for high-importance negative news
- [ ] Build a web dashboard for viewing collected data