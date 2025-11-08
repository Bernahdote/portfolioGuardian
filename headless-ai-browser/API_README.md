# Web Crawler AI - API Server

Flask API server for running AI-powered web crawler research jobs.

## Installation

Using uv (recommended):

```bash
# Install dependencies
uv pip install flask python-dotenv
```

Or using pip:

```bash
pip install flask python-dotenv
```

## Running the Server

```bash
# Make sure your environment variables are set
export OPENAI_API_KEY="your-key-here"
export LPD_TOKEN="your-lightpanda-token"

# Start the server
python server.py
```

The server will start on `http://localhost:5000`

## API Endpoints

### 1. Health Check
```bash
GET /health
```

**Example:**
```bash
curl http://localhost:5000/health
```

### 2. Start Crawler Job
```bash
POST /crawl
```

**Request Body:**
```json
{
  "topic": "AAPL",
  "goal": "Monitor Apple stock for investment risks and opportunities",
  "sources": [
    "https://news.ycombinator.com",
    "https://finance.yahoo.com",
    "https://www.cnbc.com/stocks/"
  ],
  "metadata": {
    "maxStepsPerSource": 20
  }
}
```

**Example:**
```bash
curl -X POST http://localhost:5000/crawl \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "AAPL",
    "goal": "Find recent news about Apple stock performance and any potential risks",
    "sources": ["https://news.ycombinator.com", "https://www.cnbc.com/stocks/"],
    "metadata": {"maxStepsPerSource": 15}
  }'
```

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "topic": "AAPL",
  "goal": "Find recent news about Apple stock performance and any potential risks",
  "sources": [...],
  "created_at": "2025-11-08T12:00:00"
}
```

### 3. Get Job Status
```bash
GET /jobs/<job_id>
```

**Example:**
```bash
curl http://localhost:5000/jobs/550e8400-e29b-41d4-a716-446655440000
```

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "topic": "AAPL",
  "goal": "Find recent news about Apple stock performance and any potential risks",
  "status": "completed",
  "created_at": "2025-11-08T12:00:00",
  "started_at": "2025-11-08T12:00:01",
  "completed_at": "2025-11-08T12:05:00",
  "result": {
    "topic": "AAPL",
    "goal": "Find recent news about Apple stock performance and any potential risks",
    "articlesCollected": 5,
    "thoughtsRecorded": 3,
    "sourcesProcessed": 2
  }
}
```

### 4. List All Jobs
```bash
GET /jobs
```

**Example:**
```bash
curl http://localhost:5000/jobs
```

### 5. Delete Job
```bash
DELETE /jobs/<job_id>
```

**Example:**
```bash
curl -X DELETE http://localhost:5000/jobs/550e8400-e29b-41d4-a716-446655440000
```

## Job Status Values

- `queued` - Job is waiting to start
- `running` - Job is currently executing
- `completed` - Job finished successfully
- `failed` - Job encountered an error

## Example Workflow

1. **Start a crawler job:**
```bash
JOB_ID=$(curl -s -X POST http://localhost:5000/crawl \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "TSLA",
    "goal": "Research Tesla stock news and market sentiment",
    "sources": ["https://www.cnbc.com/stocks/"],
    "metadata": {"maxStepsPerSource": 10}
  }' | jq -r '.job_id')

echo "Job ID: $JOB_ID"
```

2. **Check job status:**
```bash
curl http://localhost:5000/jobs/$JOB_ID | jq
```

3. **Wait for completion and get results:**
```bash
while true; do
  STATUS=$(curl -s http://localhost:5000/jobs/$JOB_ID | jq -r '.status')
  echo "Status: $STATUS"

  if [ "$STATUS" = "completed" ] || [ "$STATUS" = "failed" ]; then
    curl -s http://localhost:5000/jobs/$JOB_ID | jq
    break
  fi

  sleep 5
done
```

## Notes

- The API key can be provided either via environment variable (`OPENAI_API_KEY`) or in the metadata field of the request
- Jobs run in background threads and don't block the API
- Results are stored in the `sessions/` directory with timestamped folders
- The server runs in debug mode by default for development