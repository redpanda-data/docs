import os
import sys
import requests
import re
import json
import logging
import glob

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def fetch_metrics(url):
    """Fetch metrics from the given URL."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        logging.error(f"Error fetching metrics from {url}: {e}")
        return None

def parse_metrics(metrics_text):
    """
    Parse metrics text into a structured dictionary.
    Logs metrics that do not have a # TYPE entry.
    """
    metrics = {}
    lines = metrics_text.splitlines()
    current_metric = None

    for line in lines:
        if line.startswith("# HELP"):
            # Extract metric name and description
            match = re.match(r"# HELP (\S+) (.+)", line)
            if match:
                current_metric = match.group(1)
                description = match.group(2)
                metrics[current_metric] = {"description": description, "type": None, "labels": {}}
        elif line.startswith("# TYPE"):
            # Extract metric type
            if current_metric:
                match = re.match(r"# TYPE (\S+) (\S+)", line)
                if match and match.group(1) == current_metric:
                    metrics[current_metric]["type"] = match.group(2)
        elif current_metric and not line.startswith("#"):
            # Extract labels and values
            match = re.match(r"(\S+)\{(.+)\} (.+)", line)
            if match:
                metric_name = match.group(1)
                if metric_name == current_metric:
                    labels = match.group(2)
                    label_keys = [item.split("=")[0] for item in labels.split(",")]
                    metrics[current_metric]["labels"] = label_keys

    logging.info(f"Extracted {len(metrics)} metrics.")

    # Log metrics without a type
    for metric, data in metrics.items():
        if data["type"] is None:
            logging.warning(f"Metric '{metric}' does not have an associated # TYPE entry.")
    return metrics

def output_asciidoc(metrics, adoc_file):
    """Output metrics as AsciiDoc."""
    with open(adoc_file, "w") as f:
        for name, data in metrics.items():
            f.write(f"=== {name}\n\n")
            f.write(f"{data['description']}\n\n")
            f.write(f"*Type*: {data['type']}")
            if data["labels"]:
                f.write("\n\n*Labels*:\n")
                for label in data["labels"]:
                    f.write(f"\n- `{label}`")
            f.write("\n\n---\n\n")
    logging.info(f"AsciiDoc output written to {adoc_file}")

def output_json(metrics, json_file):
    """Output metrics as JSON."""
    with open(json_file, "w") as f:
        json.dump(metrics, f, indent=4)
    logging.info(f"JSON output written to {json_file}")

def ensure_directory_exists(directory):
    """Ensure the given directory exists."""
    if not os.path.exists(directory):
        os.makedirs(directory)

def find_largest_version_in_gen(gen_path):
    """
    Finds the directory in `gen_path` with the greatest semantic version number.
    Ignores 'latest' or other non-version dirs.
    """
    dirs = []
    for item in os.listdir(gen_path):
        full_path = os.path.join(gen_path, item)
        # Only consider directories that look like "X.Y" or "X.Y.Z"
        if os.path.isdir(full_path) and re.match(r'^\d+(\.\d+){1,2}$', item):
            dirs.append(item)

    if not dirs:
        return None

    # Sort as semantic versions by splitting on dots
    def version_tuple(v):
        return tuple(map(int, v.split(".")))
    dirs.sort(key=version_tuple)  # sorts ascending
    return dirs[-1]  # largest version

if __name__ == "__main__":
    # Read the tag from the script; if none provided, assume "latest"
    tag = "latest"
    if len(sys.argv) > 1:
        tag = sys.argv[1]

    # Convert "24.3.3" -> "24.3"
    # If tag is not "latest", strip the last dot.number
    if tag.lower() != "latest":
        parts = tag.split(".")
        if len(parts) >= 2:
            tag_modified = ".".join(parts[:-1])
        else:
            tag_modified = tag
    else:
        tag_modified = None

    gen_path = os.path.join(os.path.dirname(__file__), "..", "..", "gen")
    gen_path = os.path.abspath(gen_path)

    if not os.path.isdir(gen_path):
        logging.error(f"gen folder not found at: {gen_path}")
        sys.exit(1)

    if tag_modified is None:
        # If "latest", find the largest version folder inside docs/gen
        folder = find_largest_version_in_gen(gen_path)
        if not folder:
            logging.error("No version folder found in docs/gen. Exiting.")
            sys.exit(1)
        tag_modified = folder
        logging.info(f"No tag provided or 'latest' used. Using largest version folder: {tag_modified}")

    output_dir = os.path.join(gen_path, tag_modified, "metrics")
    ensure_directory_exists(output_dir)

    # Fetch and process public metrics
    METRICS_URL = "http://localhost:19644/public_metrics/"
    metrics_text = fetch_metrics(METRICS_URL)

    if not metrics_text:
        logging.error("No public metrics retrieved. Exiting.")
        sys.exit(1)

    public_metrics = parse_metrics(metrics_text)

    # Fetch and process internal metrics from /metrics endpoint
    INTERNAL_METRICS_URL = "http://localhost:19644/metrics/"
    internal_metrics_text = fetch_metrics(INTERNAL_METRICS_URL)
    if internal_metrics_text:
        internal_metrics = parse_metrics(internal_metrics_text)
    else:
        logging.error("No internal metrics retrieved.")
        internal_metrics = {}

    # Merge public and internal metrics into one JSON structure
    merged_metrics = {
        "public": public_metrics,
        "internal": internal_metrics
    }

    JSON_OUTPUT_FILE = os.path.join(output_dir, "metrics.json")
    ASCIIDOC_OUTPUT_FILE = os.path.join(output_dir, "metrics.adoc")
    INTERNAL_ASCIIDOC_OUTPUT_FILE = os.path.join(output_dir, "internal-metrics.adoc")

    output_json(merged_metrics, JSON_OUTPUT_FILE)
    output_asciidoc(public_metrics, ASCIIDOC_OUTPUT_FILE)
    output_asciidoc(internal_metrics, INTERNAL_ASCIIDOC_OUTPUT_FILE)
