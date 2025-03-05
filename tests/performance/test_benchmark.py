"""Benchmarking and profiling tests for FastChain AI."""
import time
import requests
import statistics
from typing import List, Dict
import json

class BenchmarkTest:
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.headers = {"Content-Type": "application/json"}
        self.results: Dict[str, List[float]] = {}

    def _time_request(self, method: str, endpoint: str, data: dict = None) -> float:
        """Time a single request."""
        start_time = time.time()
        if method.upper() == "GET":
            requests.get(f"{self.base_url}{endpoint}", headers=self.headers)
        elif method.upper() == "POST":
            requests.post(f"{self.base_url}{endpoint}", 
                        headers=self.headers,
                        json=data)
        return time.time() - start_time

    def benchmark_endpoint(self, name: str, method: str, endpoint: str, 
                         data: dict = None, iterations: int = 100) -> Dict:
        """Benchmark a specific endpoint."""
        times = []
        for _ in range(iterations):
            try:
                response_time = self._time_request(method, endpoint, data)
                times.append(response_time)
            except Exception as e:
                print(f"Error during benchmark {name}: {e}")
        
        if times:
            stats = {
                "min": min(times),
                "max": max(times),
                "mean": statistics.mean(times),
                "median": statistics.median(times),
                "p95": statistics.quantiles(times, n=20)[18],  # 95th percentile
                "std_dev": statistics.stdev(times) if len(times) > 1 else 0
            }
            self.results[name] = stats
            return stats
        return {}

    def run_benchmarks(self):
        """Run all benchmarks."""
        # Test chat endpoint
        self.benchmark_endpoint(
            "chat_post",
            "POST",
            "/api/v1/chat/",
            {"message": "Benchmark test message", "context": {"test": True}}
        )

        # Test intent classification
        self.benchmark_endpoint(
            "intent_classification",
            "POST",
            "/api/v1/intent/classify",
            {"text": "Test intent", "context": {"domain": "test"}}
        )

        # Test system status
        self.benchmark_endpoint(
            "system_status",
            "GET",
            "/api/v1/system/status"
        )

        # Test agent registry
        self.benchmark_endpoint(
            "agent_registry",
            "GET",
            "/api/v1/agents/registry/"
        )

    def print_results(self):
        """Print benchmark results in a formatted way."""
        print("\nBenchmark Results:")
        print("=" * 80)
        for endpoint, stats in self.results.items():
            print(f"\nEndpoint: {endpoint}")
            print("-" * 40)
            for metric, value in stats.items():
                print(f"{metric:>8}: {value:.4f}s")

def run_benchmarks():
    """Run all benchmarks and print results."""
    benchmark = BenchmarkTest()
    benchmark.run_benchmarks()
    benchmark.print_results()

if __name__ == "__main__":
    run_benchmarks()
