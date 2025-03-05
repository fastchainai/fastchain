def format_metric_name(name):
    """
    Convert a metric name to lower case and replace spaces with underscores.
    """
    return name.lower().replace(" ", "_")


def merge_tags(default_tags, tags):
    """
    Merge default tags with per-metric tags.
    """
    merged = default_tags.copy()
    if tags:
        merged.update(tags)
    return merged
