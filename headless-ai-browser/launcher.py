#!/usr/bin/env python3
"""
Multi-browser launcher for AI-powered web scraping.
Spawns multiple Node.js scraper instances with different configurations.
"""

import subprocess
import json
import sys
from typing import List, Dict, Optional
import threading
import queue


class ScraperInstance:
    """Represents a single scraper instance configuration."""

    def __init__(self, link: str, prompt: str, metadata: Optional[Dict] = None):
        self.link = link
        self.prompt = prompt
        self.metadata = metadata or {}

    def to_args(self) -> List[str]:
        """Convert to command-line arguments."""
        args = ['node', 'index.js', self.link, self.prompt]
        if self.metadata:
            args.append(json.dumps(self.metadata))
        return args


class ScraperLauncher:
    """Manages multiple scraper instances."""

    def __init__(self, base_port: int = 9222):
        self.base_port = base_port
        self.instances: List[ScraperInstance] = []

    def add_instance(self, link: str, prompt: str, metadata: Optional[Dict] = None):
        """Add a scraper instance to the queue."""
        # Auto-assign port if not specified
        if metadata is None:
            metadata = {}
        if 'port' not in metadata:
            metadata['port'] = self.base_port + len(self.instances)

        instance = ScraperInstance(link, prompt, metadata)
        self.instances.append(instance)
        return instance

    def run_instance(self, instance: ScraperInstance, result_queue: queue.Queue):
        """Run a single scraper instance."""
        try:
            print(f"Starting scraper for {instance.link} on port {instance.metadata.get('port', 9222)}")

            result = subprocess.run(
                instance.to_args(),
                capture_output=True,
                text=True,
                timeout=120  # 2 minute timeout
            )

            output = {
                'link': instance.link,
                'prompt': instance.prompt,
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }

            result_queue.put(output)

        except subprocess.TimeoutExpired:
            result_queue.put({
                'link': instance.link,
                'prompt': instance.prompt,
                'success': False,
                'error': 'Timeout after 120 seconds'
            })
        except Exception as e:
            result_queue.put({
                'link': instance.link,
                'prompt': instance.prompt,
                'success': False,
                'error': str(e)
            })

    def run_all_parallel(self) -> List[Dict]:
        """Run all instances in parallel."""
        result_queue = queue.Queue()
        threads = []

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
        """Run all instances sequentially."""
        results = []
        result_queue = queue.Queue()

        for instance in self.instances:
            self.run_instance(instance, result_queue)
            results.append(result_queue.get())

        return results


def example_usage():
    """Example of how to use the launcher."""

    launcher = ScraperLauncher(base_port=9222)

    # Example 1: Scrape Hacker News
    launcher.add_instance(
        link="https://news.ycombinator.com",
        prompt="Search for 'AI' and extract the top 5 article titles and URLs",
        metadata={"maxSteps": 15}
    )

    # Example 2: Scrape a different site
    launcher.add_instance(
        link="https://example.com",
        prompt="Find the main heading and all paragraph text",
        metadata={"maxSteps": 5}
    )

    # Example 3: Another instance with custom settings
    launcher.add_instance(
        link="https://news.ycombinator.com",
        prompt="Find the newest articles posted in the last hour",
        metadata={"maxSteps": 10}
    )

    # Run all in parallel
    print("Running scrapers in parallel...")
    results = launcher.run_all_parallel()

    # Print results
    for i, result in enumerate(results, 1):
        print(f"\n{'='*60}")
        print(f"Result {i}: {result['link']}")
        print(f"Success: {result['success']}")
        if result['success']:
            print(f"Output:\n{result['stdout']}")
        else:
            print(f"Error: {result.get('error', result.get('stderr', 'Unknown error'))}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "example":
        example_usage()
    else:
        print("AI-Powered Web Scraper Launcher")
        print("=" * 60)
        print("\nUsage:")
        print("  python launcher.py example           - Run example scrapers")
        print("\nOr use as a library:")
        print("  from launcher import ScraperLauncher")
        print("  launcher = ScraperLauncher()")
        print("  launcher.add_instance(link, prompt, metadata)")
        print("  results = launcher.run_all_parallel()")
        print("\nExample:")
        print('  launcher.add_instance(')
        print('      link="https://news.ycombinator.com",')
        print('      prompt="Search for AI and extract results",')
        print('      metadata={"port": 9222, "maxSteps": 15}')
        print('  )')
