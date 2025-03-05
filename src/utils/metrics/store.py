class MetricStore:
    def __init__(self):
        # Internal dictionary to store metrics.
        # Keys are tuples: (metric_type, name, frozenset of tag items)
        self._metrics = {}

    def record(self, metric_type, name, value, tags):
        key = (metric_type, name, frozenset(tags.items()) if tags else frozenset())
        if metric_type == "counter":
            self._metrics[key] = self._metrics.get(key, 0) + value
        elif metric_type == "gauge":
            self._metrics[key] = value
        elif metric_type == "histogram":
            if key not in self._metrics:
                self._metrics[key] = []
            self._metrics[key].append(value)
        else:
            self._metrics[key] = value

    def get_metrics(self):
        """
        Get the current metrics data without flushing.

        Returns:
            dict: Current metrics data with their types and values
        """
        metrics_data = []
        for (metric_type, name, tags), value in self._metrics.items():
            metric_entry = {
                "type": metric_type,
                "name": name,
                "value": value,
                "tags": dict(tags) if tags else {}
            }
            metrics_data.append(metric_entry)
        return metrics_data

    def flush(self):
        """
        Return the current metrics data and reset the store.
        """
        data = self._metrics.copy()
        self._metrics = {}
        return data