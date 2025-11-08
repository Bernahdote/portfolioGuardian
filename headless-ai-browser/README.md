# AI-Powered Web Scraper

An intelligent web scraper that uses OpenAI to dynamically decide what actions to take on web pages. It can navigate websites, fill forms, click buttons, and extract data based on natural language prompts.

## Features

- **AI-Driven Navigation**: Uses OpenAI GPT-4 to intelligently decide what actions to take
- **Dynamic Scraping**: Just provide a URL and describe what you want - the AI figures out the rest
- **Multi-Instance Support**: Run multiple scrapers in parallel with different configurations
- **Flexible**: Works with any website without hardcoded selectors

## Installation

1. Install Node.js dependencies:
```bash
npm install openai
```

2. Set your OpenAI API key:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

## Usage

### Single Instance (Node.js)

```bash
node index.js <link> <prompt> [metadata_json]
```

**Examples:**

```bash
# Simple scraping
node index.js "https://news.ycombinator.com" "Search for 'AI' and extract the top 5 results"

# With custom metadata
node index.js "https://example.com" "Find all product prices" '{"port":9222,"maxSteps":15}'
```

### Multiple Instances (Python)

Use the Python launcher to run multiple scrapers in parallel:

```python
from launcher import ScraperLauncher

launcher = ScraperLauncher(base_port=9222)

# Add scraper instances
launcher.add_instance(
    link="https://news.ycombinator.com",
    prompt="Search for 'AI' and extract article titles",
    metadata={"maxSteps": 15}
)

launcher.add_instance(
    link="https://example.com",
    prompt="Extract all headings and paragraphs",
    metadata={"maxSteps": 10}
)

# Run all in parallel
results = launcher.run_all_parallel()

# Process results
for result in results:
    print(f"Link: {result['link']}")
    print(f"Success: {result['success']}")
    print(f"Output: {result['stdout']}")
```

Or run the example:

```bash
python launcher.py example
```

## Parameters

### Required
- `link`: The URL to scrape
- `prompt`: Natural language description of what to do

### Optional Metadata (JSON)
- `port`: Browser port (default: 9222) - use different ports for parallel instances
- `maxSteps`: Maximum AI decision steps (default: 10)
- `openaiApiKey`: OpenAI API key (overrides env var)

## How It Works

1. **Navigate**: Opens the specified URL in a browser
2. **Observe**: Extracts page context (inputs, buttons, links, text)
3. **Decide**: Asks OpenAI what action to take next
4. **Execute**: Performs the action (type, click, wait, extract)
5. **Repeat**: Continues until task is complete or max steps reached

## AI Actions

The AI can perform these actions:

- **TYPE**: Enter text into input fields
- **CLICK**: Click buttons or links
- **WAIT**: Wait for elements to appear
- **EXTRACT**: Run JavaScript to extract data
- **DONE**: Finish and return results

## Example Prompts

- "Search for 'machine learning' and extract the top 10 results"
- "Find all product names and prices on this page"
- "Navigate to the login page and extract the form fields"
- "Click on the 'News' section and get all article headlines"
- "Find contact information on this website"

## Running Multiple Scrapers

Each scraper needs its own port. The Python launcher automatically assigns ports:

```python
launcher = ScraperLauncher(base_port=9222)

# Instance 1 uses port 9222
launcher.add_instance("https://site1.com", "Extract titles")

# Instance 2 uses port 9223
launcher.add_instance("https://site2.com", "Find prices")

# Instance 3 uses port 9224
launcher.add_instance("https://site3.com", "Get contacts")

# Run all at once
results = launcher.run_all_parallel()
```

## Troubleshooting

- **Port conflicts**: If you get port errors, make sure each instance uses a different port
- **Timeout errors**: Increase `maxSteps` in metadata for complex tasks
- **API errors**: Verify your OpenAI API key is set correctly
- **Extraction failures**: Make your prompt more specific about what data to extract

## Notes

- The scraper uses `gpt-4o-mini` for cost efficiency
- Each step makes an API call, so complex tasks may consume more tokens
- Progress is logged to stderr, final results to stdout
- The AI maintains conversation history to understand context across steps