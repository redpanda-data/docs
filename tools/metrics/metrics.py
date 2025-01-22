import requests
import re
import json
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def fetch_metrics(url):
    """Fetch metrics from the given URL."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        logging.error(f"Error fetching metrics: {e}")
        return None

def parse_metrics(metrics_text):
    """
    Parse metrics text into a structured dictionary.
    Logs metrics without a # TYPE entry.
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
                metrics[current_metric] = {"description": description, "type": None}
        elif line.startswith("# TYPE"):
            # Extract metric type
            if current_metric:
                match = re.match(r"# TYPE (\S+) (\S+)", line)
                if match and match.group(1) == current_metric:
                    metrics[current_metric]["type"] = match.group(2)
        elif current_metric and not line.startswith("#"):
            continue

    print("Extracted metrics:",len(metrics))        
    # Log metrics without a type
    for metric, data in metrics.items():
        if data["type"] is None:
            logging.warning(f"Metric '{metric}' does not have an associated # TYPE entry.")
    
    return metrics

def output_json(metrics, json_file):
    """Output metrics as JSON."""
    with open(json_file, "w") as f:
        json.dump(metrics, f, indent=4)
    logging.info(f"JSON output written to {json_file}")

def output_asciidoc(metrics, adoc_file):
    """Output metrics as AsciiDoc."""
    with open(adoc_file, "w") as f:
        for name, data in metrics.items():
            f.write(f"=== {name}\n\n")
            f.write(f"{data['description']}\n\n")
            f.write(f"*Type*: {data['type']}\n\n")
    logging.info(f"AsciiDoc output written to {adoc_file}")

def ensure_directory_exists(directory):
    """Ensure the given directory exists."""
    if not os.path.exists(directory):
        os.makedirs(directory)

if __name__ == "__main__":
    METRICS_URL = "http://localhost:19644/public_metrics/"
    OUTPUT_DIR = "gen"
    JSON_OUTPUT_FILE = os.path.join(OUTPUT_DIR, "metrics.json")
    ASCIIDOC_OUTPUT_FILE = os.path.join(OUTPUT_DIR, "metrics.adoc")

    ensure_directory_exists(OUTPUT_DIR)

    metrics_text = fetch_metrics(METRICS_URL)
    if metrics_text:
        metrics = parse_metrics(metrics_text)
        output_json(metrics, JSON_OUTPUT_FILE)
        output_asciidoc(metrics, ASCIIDOC_OUTPUT_FILE)