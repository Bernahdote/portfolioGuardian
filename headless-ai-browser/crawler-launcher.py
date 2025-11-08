#!/usr/bin/env python3
"""
Web Crawler Launcher - Run multiple research jobs across various sources
"""

import subprocess
import json
import sys
from typing import List, Dict, Optional
import threading
import queue
from datetime import datetime


class CrawlerInstance:
    """Represents a single web crawler research configuration."""

    def __init__(self, topic: str, goal: str, sources: List[str], metadata: Optional[Dict] = None):
        self.topic = topic
        self.goal = goal
        self.sources = sources
        self.metadata = metadata or {}

    def to_args(self) -> List[str]:
        """Convert to command-line arguments for stock-guardian.js."""
        args = [
            'node',
            'stock-guardian.js',
            self.topic,
            self.goal,
            json.dumps(self.sources)
        ]
        if self.metadata:
            args.append(json.dumps(self.metadata))
        return args


class CrawlerLauncher:
    """Manages multiple web crawler research instances."""

    def __init__(self):
        self.instances: List[CrawlerInstance] = []

    def add_job(self, topic: str, goal: str, sources: List[str], metadata: Optional[Dict] = None):
        """Add a research job to the queue."""
        if metadata is None:
            metadata = {}

        instance = CrawlerInstance(topic, goal, sources, metadata)
        self.instances.append(instance)
        return instance

    def run_instance(self, instance: CrawlerInstance, result_queue: queue.Queue):
        """Run a single crawler instance."""
        try:
            print(f"🔍 Starting research on: {instance.topic}")
            print(f"   Goal: {instance.goal}")
            print(f"   Sources: {', '.join(instance.sources)}")

            result = subprocess.run(
                instance.to_args(),
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )

            output = {
                'topic': instance.topic,
                'goal': instance.goal,
                'sources': instance.sources,
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode,
                'timestamp': datetime.now().isoformat()
            }

            result_queue.put(output)

        except subprocess.TimeoutExpired:
            result_queue.put({
                'topic': instance.topic,
                'goal': instance.goal,
                'sources': instance.sources,
                'success': False,
                'error': 'Timeout after 600 seconds',
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            result_queue.put({
                'topic': instance.topic,
                'goal': instance.goal,
                'sources': instance.sources,
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })

    def run_all_parallel(self) -> List[Dict]:
        """Run all crawler instances in parallel."""
        result_queue = queue.Queue()
        threads = []

        print(f"\n{'='*60}")
        print(f"🔍 Web Crawler AI - Running {len(self.instances)} jobs in parallel")
        print(f"{'='*60}\n")

        for instance in self.instances:
            thread = threading.Thread(
                target=self.run_instance,
                args=(instance, result_queue)
            )
            thread.start()
            threads.append(thread)

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Collect results
        results = []
        while not result_queue.empty():
            results.append(result_queue.get())

        return results

    def run_all_sequential(self) -> List[Dict]:
        """Run all crawler instances sequentially."""
        results = []
        result_queue = queue.Queue()

        print(f"\n{'='*60}")
        print(f"🔍 Web Crawler AI - Running {len(self.instances)} jobs sequentially")
        print(f"{'='*60}\n")

        for instance in self.instances:
            self.run_instance(instance, result_queue)
            results.append(result_queue.get())

        return results


def example_stocks():
    """Example: Monitor multiple stocks for investment research."""

    launcher = CrawlerLauncher()

    # Define common news sources
    tech_sources = [
        "https://news.ycombinator.com",
        "https://techcrunch.com",
    ]

    financial_sources = [
        "https://finance.yahoo.com",
        "https://www.cnbc.com/stocks/",
    ]

    # Research Apple
    launcher.add_job(
        topic="AAPL",
        goal="Monitor Apple stock for investment risks and opportunities. Focus on recent news, earnings, and market sentiment.",
        sources=tech_sources,
        metadata={"maxStepsPerSource": 15}
    )

    # Research Microsoft
    launcher.add_job(
        topic="MSFT",
        goal="Find recent news about Microsoft stock performance and any potential risks or growth opportunities.",
        sources=tech_sources,
        metadata={"maxStepsPerSource": 15}
    )

    # Research NVIDIA
    launcher.add_job(
        topic="NVDA",
        goal="Research NVIDIA stock with focus on AI chip market and competition.",
        sources=financial_sources,
        metadata={"maxStepsPerSource": 15}
    )

    # Run all in parallel
    results = launcher.run_all_parallel()

    # Print summary
    print(f"\n{'='*60}")
    print("📊 RESEARCH SUMMARY")
    print(f"{'='*60}\n")

    for result in results:
        print(f"Topic: {result['topic']}")
        print(f"Goal: {result['goal'][:60]}...")
        print(f"Success: {result['success']}")
        if result['success']:
            try:
                output_data = json.loads(result['stdout'].split('\n')[-2])
                print(f"Articles collected: {output_data.get('articlesCollected', 0)}")
                print(f"Thoughts recorded: {output_data.get('thoughtsRecorded', 0)}")
            except:
                print("Output parsing failed")
        else:
            print(f"Error: {result.get('error', result.get('stderr', 'Unknown'))}")
        print()


def example_tech_research():
    """Example: Research various tech topics."""

    launcher = CrawlerLauncher()

    sources = [
        "https://news.ycombinator.com",
        "https://techcrunch.com",
    ]

    # Research AI developments
    launcher.add_job(
        topic="AI and Machine Learning",
        goal="Find recent breakthroughs and trends in AI and machine learning technology.",
        sources=sources,
        metadata={"maxStepsPerSource": 20}
    )

    # Research cybersecurity
    launcher.add_job(
        topic="Cybersecurity",
        goal="Research recent security breaches, vulnerabilities, and best practices.",
        sources=sources,
        metadata={"maxStepsPerSource": 15}
    )

    results = launcher.run_all_parallel()

    for result in results:
        print(f"\n{'='*60}")
        print(f"Topic: {result['topic']}")
        print(f"Success: {result['success']}")
        if result['success']:
            print(f"Output:\n{result['stdout'][-500:]}")  # Last 500 chars
        else:
            print(f"Error: {result.get('error', result.get('stderr', 'Unknown'))}")


def example_custom():
    """Example: Custom research job."""

    if len(sys.argv) < 4:
        print("Usage: python crawler-launcher.py custom <topic> <goal> <source1> <source2> ...")
        print('Example: python crawler-launcher.py custom "TSLA" "Find Tesla stock news" https://news.ycombinator.com')
        sys.exit(1)

    topic = sys.argv[2]
    goal = sys.argv[3]
    sources = sys.argv[4:]

    launcher = CrawlerLauncher()
    launcher.add_job(topic, goal, sources, {"maxStepsPerSource": 20})

    results = launcher.run_all_sequential()

    for result in results:
        print(f"\n{'='*60}")
        print(f"Topic: {result['topic']}")
        print(f"Goal: {result['goal']}")
        print(f"Success: {result['success']}")
        if result['success']:
            print(f"Output:\n{result['stdout']}")
        else:
            print(f"Error: {result.get('error', result.get('stderr', 'Unknown'))}")


def main():
    """Main entry point."""

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "stocks":
            example_stocks()
        elif command == "tech":
            example_tech_research()
        elif command == "custom":
            example_custom()
        else:
            print(f"Unknown command: {command}")
            print_usage()
    else:
        print_usage()


def print_usage():
    """Print usage instructions."""
    print("Web Crawler AI Launcher")
    print("=" * 60)
    print("\nUsage:")
    print("  python crawler-launcher.py stocks          - Monitor multiple stocks")
    print("  python crawler-launcher.py tech            - Research tech topics")
    print('  python crawler-launcher.py custom <topic> <goal> <sources...>')
    print("                                             - Custom research job")
    print("\nOr use as a library:")
    print("  from crawler_launcher import CrawlerLauncher")
    print("  launcher = CrawlerLauncher()")
    print('  launcher.add_job("AAPL", "Find Apple news", ["https://news.ycombinator.com"])')
    print("  results = launcher.run_all_parallel()")
    print("\nExample:")
    print('  launcher.add_job(')
    print('      topic="Climate Change",')
    print('      goal="Research latest climate change news and scientific findings",')
    print('      sources=["https://news.ycombinator.com", "https://www.nature.com"],')
    print('      metadata={"maxStepsPerSource": 20}')
    print('  )')


if __name__ == "__main__":
    main()
