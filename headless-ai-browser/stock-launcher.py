#!/usr/bin/env python3
"""
Stock Guardian Launcher - Monitor multiple stocks across various news sources
"""

import subprocess
import json
import sys
from typing import List, Dict, Optional
import threading
import queue
from datetime import datetime


class StockMonitorInstance:
    """Represents a single stock monitoring configuration."""

    def __init__(self, ticker: str, sources: List[str], metadata: Optional[Dict] = None):
        self.ticker = ticker
        self.sources = sources
        self.metadata = metadata or {}

    def to_args(self) -> List[str]:
        """Convert to command-line arguments for stock-guardian.js."""
        args = [
            'node',
            'stock-guardian.js',
            self.ticker,
            json.dumps(self.sources)
        ]
        if self.metadata:
            args.append(json.dumps(self.metadata))
        return args


class StockGuardianLauncher:
    """Manages multiple stock monitoring instances."""

    def __init__(self, base_port: int = 9222):
        self.base_port = base_port
        self.instances: List[StockMonitorInstance] = []

    def add_stock(self, ticker: str, sources: List[str], metadata: Optional[Dict] = None):
        """Add a stock to monitor."""
        if metadata is None:
            metadata = {}

        # Auto-assign port if not specified
        if 'port' not in metadata:
            metadata['port'] = self.base_port + len(self.instances)

        instance = StockMonitorInstance(ticker, sources, metadata)
        self.instances.append(instance)
        return instance

    def run_instance(self, instance: StockMonitorInstance, result_queue: queue.Queue):
        """Run a single stock monitoring instance."""
        try:
            print(f"🔍 Starting monitoring for {instance.ticker} on port {instance.metadata.get('port', 9222)}")
            print(f"   Sources: {', '.join(instance.sources)}")

            result = subprocess.run(
                instance.to_args(),
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )

            output = {
                'ticker': instance.ticker,
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
                'ticker': instance.ticker,
                'sources': instance.sources,
                'success': False,
                'error': 'Timeout after 600 seconds',
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            result_queue.put({
                'ticker': instance.ticker,
                'sources': instance.sources,
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })

    def run_all_parallel(self) -> List[Dict]:
        """Run all stock monitoring instances in parallel."""
        result_queue = queue.Queue()
        threads = []

        print(f"\n{'='*60}")
        print(f"📊 Stock Guardian - Monitoring {len(self.instances)} stocks in parallel")
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
        """Run all stock monitoring instances sequentially."""
        results = []
        result_queue = queue.Queue()

        print(f"\n{'='*60}")
        print(f"📊 Stock Guardian - Monitoring {len(self.instances)} stocks sequentially")
        print(f"{'='*60}\n")

        for instance in self.instances:
            self.run_instance(instance, result_queue)
            results.append(result_queue.get())

        return results


def example_tech_stocks():
    """Example: Monitor major tech stocks."""

    launcher = StockGuardianLauncher(base_port=9222)

    # Define common news sources for tech stocks
    tech_sources = [
        "https://news.ycombinator.com",
        "https://techcrunch.com",
    ]

    financial_sources = [
        "https://finance.yahoo.com",
        "https://www.bloomberg.com",
    ]

    # Monitor Apple
    launcher.add_stock(
        ticker="AAPL",
        sources=tech_sources,
        metadata={"maxStepsPerSource": 15}
    )

    # Monitor Microsoft
    launcher.add_stock(
        ticker="MSFT",
        sources=tech_sources,
        metadata={"maxStepsPerSource": 15}
    )

    # Monitor NVIDIA
    launcher.add_stock(
        ticker="NVDA",
        sources=financial_sources,
        metadata={"maxStepsPerSource": 15}
    )

    # Run all in parallel
    results = launcher.run_all_parallel()

    # Print summary
    print(f"\n{'='*60}")
    print("📊 MONITORING SUMMARY")
    print(f"{'='*60}\n")

    for result in results:
        print(f"Stock: {result['ticker']}")
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


def example_custom():
    """Example: Custom stock monitoring."""

    if len(sys.argv) < 3:
        print("Usage: python stock-launcher.py custom <ticker> <source1> <source2> ...")
        print("Example: python stock-launcher.py custom TSLA https://news.ycombinator.com https://techcrunch.com")
        sys.exit(1)

    ticker = sys.argv[2]
    sources = sys.argv[3:]

    launcher = StockGuardianLauncher()
    launcher.add_stock(ticker, sources, {"maxStepsPerSource": 20})

    results = launcher.run_all_sequential()

    for result in results:
        print(f"\n{'='*60}")
        print(f"Stock: {result['ticker']}")
        print(f"Success: {result['success']}")
        if result['success']:
            print(f"Output:\n{result['stdout']}")
        else:
            print(f"Error: {result.get('error', result.get('stderr', 'Unknown'))}")


def main():
    """Main entry point."""

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "tech":
            example_tech_stocks()
        elif command == "custom":
            example_custom()
        else:
            print(f"Unknown command: {command}")
            print_usage()
    else:
        print_usage()


def print_usage():
    """Print usage instructions."""
    print("Stock Guardian Launcher")
    print("=" * 60)
    print("\nUsage:")
    print("  python stock-launcher.py tech              - Monitor major tech stocks")
    print("  python stock-launcher.py custom <ticker> <sources...>")
    print("                                             - Monitor custom stock")
    print("\nOr use as a library:")
    print("  from stock_launcher import StockGuardianLauncher")
    print("  launcher = StockGuardianLauncher()")
    print("  launcher.add_stock('AAPL', ['https://news.ycombinator.com'])")
    print("  results = launcher.run_all_parallel()")
    print("\nExample:")
    print('  launcher.add_stock(')
    print('      ticker="TSLA",')
    print('      sources=["https://techcrunch.com", "https://news.ycombinator.com"],')
    print('      metadata={"port": 9222, "maxStepsPerSource": 20}')
    print('  )')


if __name__ == "__main__":
    main()