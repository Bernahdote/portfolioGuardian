#!/usr/bin/env python3
"""
Flask API server for Stock Guardian AI
Allows starting monitoring jobs via HTTP API
"""

from flask import Flask, request, jsonify
import subprocess
import json
import os
import threading
import uuid
from datetime import datetime

app = Flask(__name__)

# Store running jobs
jobs = {}

def run_crawler(job_id, ticker, topic, goal, sources, metadata):
    """Run the web crawler script in a separate process"""
    try:
        # Prepare the command
        sources_json = json.dumps(sources)
        metadata_json = json.dumps(metadata)

        cmd = [
            'node',
            'stock-guardian.js',
            ticker,
            topic,
            goal,
            sources_json,
            metadata_json
        ]

        # Update job status
        jobs[job_id]['status'] = 'running'
        jobs[job_id]['started_at'] = datetime.utcnow().isoformat()

        # Run the process
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )

        # Parse the result from stdout
        try:
            result_data = json.loads(result.stdout.strip())
            jobs[job_id]['result'] = result_data
            jobs[job_id]['status'] = 'completed'
        except json.JSONDecodeError:
            jobs[job_id]['result'] = {
                'error': 'Failed to parse result',
                'stdout': result.stdout,
                'stderr': result.stderr
            }
            jobs[job_id]['status'] = 'failed'

        jobs[job_id]['completed_at'] = datetime.utcnow().isoformat()
        jobs[job_id]['return_code'] = result.returncode

    except Exception as e:
        jobs[job_id]['status'] = 'failed'
        jobs[job_id]['error'] = str(e)
        jobs[job_id]['completed_at'] = datetime.utcnow().isoformat()


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Web Crawler AI',
        'timestamp': datetime.utcnow().isoformat()
    })


@app.route('/crawl', methods=['POST'])
def start_crawl():
    """
    Start a web crawler job

    Request body:
    {
        "ticker": "AAPL",
        "topic": "Apple Inc",
        "goal": "Monitor Apple stock for investment risks and opportunities",
        "sources": ["https://news.ycombinator.com", "https://finance.yahoo.com"],
        "metadata": {
            "maxStepsPerSource": 20,
            "openaiApiKey": "sk-..."  // Optional, will use env var if not provided
        }
    }

    Returns:
    {
        "job_id": "uuid",
        "status": "queued",
        "ticker": "AAPL",
        "topic": "Apple Inc",
        "goal": "...",
        "created_at": "2025-11-08T12:00:00"
    }
    """
    data = request.get_json()

    # Validate required fields
    if not data:
        return jsonify({'error': 'Request body required'}), 400

    ticker = data.get('ticker')
    topic = data.get('topic')
    goal = data.get('goal')
    sources = data.get('sources')

    if not ticker:
        return jsonify({'error': 'ticker is required'}), 400

    if not topic:
        return jsonify({'error': 'topic is required'}), 400

    if not goal:
        return jsonify({'error': 'goal is required'}), 400

    if not sources or not isinstance(sources, list):
        return jsonify({'error': 'sources must be a non-empty array'}), 400

    # Optional metadata
    metadata = data.get('metadata', {})

    # Create job
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        'job_id': job_id,
        'ticker': ticker,
        'topic': topic,
        'goal': goal,
        'sources': sources,
        'metadata': metadata,
        'status': 'queued',
        'created_at': datetime.utcnow().isoformat(),
        'started_at': None,
        'completed_at': None,
        'result': None,
        'error': None
    }

    # Start crawler in background thread
    thread = threading.Thread(
        target=run_crawler,
        args=(job_id, ticker, topic, goal, sources, metadata)
    )
    thread.daemon = True
    thread.start()

    return jsonify({
        'job_id': job_id,
        'status': 'queued',
        'ticker': ticker,
        'topic': topic,
        'goal': goal,
        'sources': sources,
        'created_at': jobs[job_id]['created_at']
    }), 202


@app.route('/jobs/<job_id>', methods=['GET'])
def get_job(job_id):
    """
    Get status of a monitoring job

    Returns:
    {
        "job_id": "uuid",
        "ticker": "AAPL",
        "status": "running|completed|failed",
        "created_at": "...",
        "started_at": "...",
        "completed_at": "...",
        "result": {...}  // Only if completed
    }
    """
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404

    return jsonify(jobs[job_id])


@app.route('/jobs', methods=['GET'])
def list_jobs():
    """
    List all monitoring jobs

    Returns:
    {
        "jobs": [...]
    }
    """
    return jsonify({
        'jobs': list(jobs.values()),
        'count': len(jobs)
    })


@app.route('/jobs/<job_id>', methods=['DELETE'])
def delete_job(job_id):
    """Delete a job from the list"""
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404

    del jobs[job_id]
    return jsonify({'message': 'Job deleted', 'job_id': job_id})


if __name__ == '__main__':
    # Get port from environment or default to 5000
    port = int(os.environ.get('PORT', 5000))

    print(f"""
╔═══════════════════════════════════════════════════════╗
║         CUA SCRAPER - API Server                  ║
╚═══════════════════════════════════════════════════════╝

Server running on http://localhost:{port}

Endpoints:
  GET  /health           - Health check
  POST /crawl            - Start crawler job
  GET  /jobs             - List all jobs
  GET  /jobs/<job_id>    - Get job status
  DELETE /jobs/<job_id>  - Delete job

Example request:
  curl -X POST http://localhost:{port}/crawl \\
    -H "Content-Type: application/json" \\
    -d '{{
    "ticker" : "AAPL",
      "topic": "New releases",
      "goal": "Find news about new products from apple",
      "sources": ["https://news.ycombinator.com"],
      "metadata": {{"maxStepsPerSource": 10}}
    }}'

""")

    app.run(host='0.0.0.0', port=port, debug=True)
