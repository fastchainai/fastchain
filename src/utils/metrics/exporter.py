from abc import ABC, abstractmethod


class Exporter(ABC):
    @abstractmethod
    def export(self, metrics):
        """
        Export the given metrics.
        :param metrics: Dictionary of metrics data.
        """
        pass


class PrometheusExporter(Exporter):
    def __init__(self, host="0.0.0.0", port=8000):
        self.host = host
        self.port = port
        self.metrics_data = {}

        # Start a simple HTTP server in a separate thread to expose metrics.
        from http.server import BaseHTTPRequestHandler, HTTPServer
        import threading

        class MetricsHandler(BaseHTTPRequestHandler):
            def do_GET(inner_self):
                response = ""
                for metric in self.metrics_data.values():
                    response += metric + "\n"
                inner_self.send_response(200)
                inner_self.send_header("Content-type", "text/plain")
                inner_self.end_headers()
                inner_self.wfile.write(response.encode())

        self.handler = MetricsHandler
        self.server = HTTPServer((self.host, self.port), self.handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def export(self, metrics):
        """
        Export metrics by converting them to Prometheus text format.
        """
        lines = []
        for key, data in metrics.items():
            # key: (metric_type, name, tags)
            metric_type, name, tags = key
            tag_str = (
                ",".join(f'{k}="{v}"' for k, v in dict(tags).items())
                if tags
                else ""
            )
            lines.append(f"{metric_type}:{name}{{{tag_str}}} {data}")
        self.metrics_data = {i: line for i, line in enumerate(lines)}


class DatadogExporter(Exporter):
    def __init__(self, api_key):
        self.api_key = api_key

    def export(self, metrics):
        """
        Simulate exporting metrics to Datadog by printing them.
        In a production scenario, this method would call the Datadog API.
        """
        print("Exporting metrics to Datadog:")
        for key, data in metrics.items():
            metric_type, name, tags = key
            tag_str = (
                ",".join(f"{k}:{v}" for k, v in dict(tags).items()) if tags else ""
            )
            print(f"{metric_type}.{name} [{tag_str}]: {data}")
