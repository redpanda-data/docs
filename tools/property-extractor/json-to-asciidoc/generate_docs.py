import json
import os
import re
import argparse

# --- Constants for Paths and Filenames ---
INPUT_JSON_PATH = "gen/"
INPUT_JSON_FILE = "properties-output.json"

OUTPUT_DIR_DEFAULT = "output"
PAGE_FOLDER_NAME = "pages"
ERROR_FOLDER_NAME = "error"

OUTPUT_FILE_BROKER = "broker-properties.adoc"
OUTPUT_FILE_CLUSTER = "cluster-properties.adoc"
OUTPUT_FILE_CLOUD = "object-storage-properties.adoc"
OUTPUT_FILE_DEPRECATED = os.path.join("deprecated", "partials", "deprecated-properties.adoc")
ALL_PROPERTIES_FILE = "all_properties.txt"

ERROR_FILE_DESCRIPTION = "empty_description.txt"
ERROR_FILE_TYPE = "empty_type.txt"
ERROR_FILE_MAX_WITHOUT_MIN = "max_without_min.txt"
ERROR_FILE_MIN_WITHOUT_MAX = "min_without_max.txt"

# --- Static Documentation Strings ---
BROKER_PAGE_TITLE = (
    "= Broker Configuration Properties\n"
    ":page-aliases: reference:node-properties.adoc, reference:node-configuration-sample.adoc\n"
    ":description: Reference of broker configuration properties.\n\n"
)
BROKER_INTRO = (
    "Broker configuration properties are applied individually to each broker in a cluster. "
    "You can find and modify these properties in the `redpanda.yaml` configuration file.\n\n"
    "For information on how to edit broker properties, see xref:manage:cluster-maintenance/node-property-configuration.adoc[].\n\n"
    "NOTE: All broker properties require that you restart Redpanda for any update to take effect.\n\n"
)
BROKER_TITLE = "== Broker configuration\n\n"

SCHEMA_REGISTRY_TITLE = "== Schema Registry\n\n"
PANDAPROXY_TITLE = "== HTTP Proxy\n\n"
KAFKA_CLIENT_TITLE = "== HTTP Proxy Client\n\n"

SCHEMA_REGISTRY_INTRO = (
    "The Schema Registry provides configuration properties to help you enable producers and consumers "
    "to share information needed to serialize and deserialize producer and consumer messages.\n\n"
    "For information on how to edit broker properties for the Schema Registry, see xref:manage:cluster-maintenance/node-property-configuration.adoc[].\n\n"
)
PANDAPROXY_INTRO = (
    "Redpanda HTTP Proxy allows access to your data through a REST API. For example, you can list topics or brokers, "
    "get events, produce events, subscribe to events from topics using consumer groups, and commit offsets for a consumer.\n\n"
    "See xref:develop:http-proxy.adoc[]\n\n"
)
KAFKA_CLIENT_INTRO = "Configuration options for HTTP Proxy Client.\n\n"

CLUSTER_PAGE_TITLE = (
    "= Cluster Configuration Properties\n"
    ":page-aliases: reference:tunable-properties.adoc, reference:cluster-properties.adoc\n"
    ":description: Cluster configuration properties list.\n\n"
)
CLUSTER_CONFIG_INTRO = (
    "Cluster configuration properties are the same for all brokers in a cluster, and are set at the cluster level.\n\n"
    "For information on how to edit cluster properties, see xref:manage:cluster-maintenance/cluster-property-configuration.adoc[] "
    "or xref:manage:kubernetes/k-cluster-property-configuration.adoc[].\n\n"
    "NOTE: Some cluster properties require that you restart the cluster for any updates to take effect. "
    "See the specific property details to identify whether or not a restart is required.\n\n"
)
CLUSTER_CONFIG_TITLE = "== Cluster configuration\n\n"

CLOUD_PAGE_TITLE = (
    "= Object Storage Properties\n"
    ":description: Reference of object storage properties.\n\n"
)
CLOUD_CONFIG_INTRO = (
    "Object storage properties are a type of cluster property. For information on how to edit cluster properties, "
    "see xref:manage:cluster-maintenance/cluster-property-configuration.adoc[].\n\n"
    "NOTE: Some object storage properties require that you restart the cluster for any updates to take effect. "
    "See the specific property details to identify whether or not a restart is required.\n\n"
)
CLOUD_CONFIG_TITLE = (
    "== Object storage configuration\n\n"
    "Object storage properties should only be set if you enable xref:manage:tiered-storage.adoc[Tiered Storage].\n\n"
)

DEPRECATED_PROPERTIES_TITLE = "\n== Configuration properties\n\n"
DEPRECATED_PROPERTIES_INTRO = "This is an exhaustive list of all the deprecated properties.\n\n"
DEPRECATED_BROKER_TITLE = "=== Broker properties\n\n"
DEPRECATED_CLUSTER_TITLE = "=== Cluster properties\n\n"

# --- Mapping Constants ---
DEFINED_IN_MAPPING = {
    "src/v/config/node_config.cc": "broker",
    "src/v/pandaproxy/schema_registry/configuration.cc": "schema reg",
    "src/v/pandaproxy/rest/configuration.cc": "http proxy",
    "src/v/kafka/client/configuration.cc": "http client",
    "src/v/config/configuration.cc": "cluster"
}

SUFFIX_TO_UNIT = {
    "ms": "milliseconds",
    "sec": "seconds",  # Code is not always consistent when using seconds.
    "seconds": "seconds",
    "bytes": "bytes",
    "buf": "bytes",
    "partitions": "number of partitions per topic",
    "percent": "percent",
    "bps": "bytes per second",
    "fraction": "fraction"
}

# --- Utility Functions ---
def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Generate documentation from properties JSON"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        required=True,
        help="Directory to save the generated documentation",
    )
    return parser.parse_args()

def ensure_directory_exists(directory):
    os.makedirs(directory, exist_ok=True)

def load_json(input_path, input_file):
    try:
        with open(os.path.join(input_path, input_file), "r", encoding="utf-8") as json_file:
            return json.load(json_file)
    except FileNotFoundError:
        print(f"Error: The file '{input_file}' does not exist.")
        return {}
    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse JSON in '{input_file}': {str(e)}")
        return {}

def process_defaults(input_string, suffix):
    # Test for ip:port in vector
    vector_match = re.search(
        r'std::vector<net::unresolved_address>\(\{\{("([\d.]+)",\s*(\d+))\}\}\)', input_string
    )
    if vector_match:
        ip = vector_match.group(2)
        port = vector_match.group(3)
        return [f"{ip}:{port}"]

    # Test for ip:port in single-string
    broker_match = re.search(r'net::unresolved_address\("([\d.]+)",\s*(\d+)\)', input_string)
    if broker_match:
        ip = broker_match.group(1)
        port = broker_match.group(2)
        return f"{ip}:{port}"

    # Handle single time units: seconds, milliseconds, hours, minutes
    time_match = re.search(r"(\d+)(ms|s|min|h)", input_string)
    # Handle complex time expressions like '24h*365'
    complex_match = re.search(r"(\d+)(h|min|s|ms)\s*\*\s*(\d+)", input_string)
    # Handle std::chrono::time expressions
    chrono_match = re.search(r"std::chrono::(\w+)[\{\(](\d+)[\)\}]", input_string)

    if time_match:
        value = int(time_match.group(1))
        unit = time_match.group(2)
        if suffix == "ms":
            if unit == "ms":
                return value
            elif unit == "s":
                return value * 1000
            elif unit == "min":
                return value * 60 * 1000
            elif unit == "h":
                return value * 60 * 60 * 1000
        elif suffix == "sec":
            if unit == "s":
                return value
            elif unit == "min":
                return value * 60
            elif unit == "h":
                return value * 60 * 60
            elif unit == "ms":
                return value / 1000

    if complex_match:
        value = int(complex_match.group(1))
        unit = complex_match.group(2)
        multiplier = int(complex_match.group(3))
        if suffix == "ms":
            if unit == "h":
                return value * 60 * 60 * 1000 * multiplier
            elif unit == "min":
                return value * 60 * 1000 * multiplier
            elif unit == "s":
                return value * 1000 * multiplier
            elif unit == "ms":
                return value * multiplier
        elif suffix == "sec":
            if unit == "h":
                return value * 60 * 60 * multiplier
            elif unit == "min":
                return value * 60 * multiplier
            elif unit == "s":
                return value * multiplier
            elif unit == "ms":
                return (value * multiplier) / 1000

    if chrono_match:
        chrono_unit = chrono_match.group(1)
        chrono_value = int(chrono_match.group(2))
        chrono_conversion = {
            "milliseconds": 1,
            "seconds": 1000,
            "minutes": 60 * 1000,
            "hours": 60 * 60 * 1000,
            "days": 24 * 60 * 60 * 1000,
            "weeks": 7 * 24 * 60 * 60 * 1000,
        }
        if suffix == "ms":
            return chrono_value * chrono_conversion.get(chrono_unit, 1)
        elif suffix == "sec":
            if chrono_unit == "milliseconds":
                return chrono_value / 1000
            else:
                return (chrono_value * chrono_conversion.get(chrono_unit, 1)) / 1000

    # Return the original string if no pattern matches
    return input_string

def generate_property_doc(key, value):
    """
    Generate documentation string for a single property.
    Returns None if required fields are missing.
    """
    description = value.get("description", "").strip()
    prop_type = value.get("type", "").strip()
    if not description or not prop_type:
        return None

    # Capitalize first letter and ensure a period at the end.
    description = description[0].upper() + description[1:]
    if not description.endswith('.'):
        description += '.'

    lines = [f"=== {value.get('name')}\n\n", f"{description}\n\n"]

    property_suffix = value.get("name").split('_')[-1]
    if property_suffix in SUFFIX_TO_UNIT:
        lines.append(f"*Unit:* {SUFFIX_TO_UNIT[property_suffix]}\n\n")

    # For non-broker properties (node_config.cc indicates broker), add restart info.
    if value.get("defined_in") != "src/v/config/node_config.cc":
        restart = "Yes" if value.get("needs_restart", False) else "No"
        lines.append(f"*Requires restart:* {restart}\n\n")

    visibility = value.get("visibility") or "user"
    lines.append(f"*Visibility:* `{visibility}`\n\n")

    if prop_type in ["string", "array", "number", "boolean", "integer"]:
        lines.append(f"*Type:* {prop_type}\n\n")

    if value.get("maximum") is not None and value.get("minimum") is not None:
        lines.append(
            f"*Accepted values:* [`{value.get('minimum')}`, `{value.get('maximum')}`]\n\n"
        )

    default = value.get("default")
    if default is None or default == "":
        default_str = "null"
    elif isinstance(default, bool):
        default_str = "true" if default else "false"
    else:
        default_str = str(default).replace("'", "").lower()
        default_str = process_defaults(default_str, property_suffix)
    lines.append(f"*Default:* `{default_str}`\n\n")
    lines.append("---\n\n")
    return "".join(lines)

def write_data_to_file(output_dir, filename, data):
    file_path = os.path.join(output_dir, filename)
    ensure_directory_exists(os.path.dirname(file_path))
    try:
        with open(file_path, "w+", encoding="utf-8") as output:
            output.write(data)
        print(f"Data written to {file_path} successfully.")
        return True
    except Exception as e:
        print(f"Error writing data to {filename}: {str(e)}")
        return False

def write_error_file(output_dir, filename, error_content, total_properties):
    file_path = os.path.join(output_dir, filename)
    ensure_directory_exists(os.path.dirname(file_path))
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
        if error_content:
            error_content = error_content.rstrip("\n")
            with open(file_path, "w+", encoding="utf-8") as output:
                output.write(error_content)
            error_count = len(error_content.split("\n"))
            if error_count > 0:
                empty_name = filename.replace("empty_", "").replace(".txt", "")
                error_type = (
                    "deprecated properties"
                    if empty_name == "deprecated_properties"
                    else f"properties with empty {empty_name}"
                )
                error_percentage = round((error_count / total_properties) * 100, 2)
                print(
                    f"You have {error_count} {error_type}. Percentage of errors: {error_percentage}%. Data written in '{filename}'."
                )
    except Exception as e:
        print(f"Error writing error data to '{filename}': {str(e)}")

# --- Main Processing ---
def main():
    args = parse_arguments()
    output_dir = args.output_dir
    page_folder = os.path.join(output_dir, PAGE_FOLDER_NAME)
    error_folder = os.path.join(output_dir, ERROR_FOLDER_NAME)

    data = load_json(INPUT_JSON_PATH, INPUT_JSON_FILE)
    properties = data.get("properties", {})
    total_properties = len(properties)

    # Accumulators for property documentation and error logs.
    broker_config_content = []
    schema_registry_content = []
    pandaproxy_content = []
    kafka_client_content = []
    cluster_config_content = []
    cloud_config_content = []
    deprecated_broker_content = []
    deprecated_cluster_content = []
    all_properties = []
    empty_description_errors = []
    empty_type_errors = []
    max_without_min_errors = []
    min_without_max_errors = []
    deprecated_properties_errors = []

    for key, value in properties.items():
        all_properties.append(key)
        group = None
        if key.startswith("cloud_"):
            group = "cloud"
        else:
            group = DEFINED_IN_MAPPING.get(value.get("defined_in"))

        # Handle deprecated properties.
        if value.get("is_deprecated") is True:
            deprecated_properties_errors.append(key)
            if group == "broker":
                deprecated_broker_content.append(f"- {key}\n\n")
            elif group in ["cluster", "cloud"]:
                deprecated_cluster_content.append(f"- {key}\n\n")
            continue

        # Log errors for missing description or type.
        if not value.get("description", "").strip():
            empty_description_errors.append(key)
        if not value.get("type", "").strip():
            empty_type_errors.append(key)

        # Check for max/min inconsistencies.
        if value.get("maximum") is not None and value.get("minimum") is None:
            max_without_min_errors.append(key)
        if value.get("minimum") is not None and value.get("maximum") is None:
            min_without_max_errors.append(key)

        property_doc = generate_property_doc(key, value)
        if property_doc is None:
            continue

        group_mapping = {
            "broker": broker_config_content,
            "schema reg": schema_registry_content,
            "http proxy": pandaproxy_content,
            "http client": kafka_client_content,
            "cluster": cluster_config_content,
            "cloud": cloud_config_content,
        }
        if group in group_mapping:
            group_mapping[group].append(property_doc)

    # Construct final documentation pages.
    broker_page = (
        BROKER_PAGE_TITLE
        + BROKER_INTRO
        + BROKER_TITLE
        + "".join(broker_config_content)
        + "\n\n"
        + SCHEMA_REGISTRY_TITLE
        + SCHEMA_REGISTRY_INTRO
        + "".join(schema_registry_content)
        + "\n\n"
        + PANDAPROXY_TITLE
        + PANDAPROXY_INTRO
        + "".join(pandaproxy_content)
        + "\n\n"
        + KAFKA_CLIENT_TITLE
        + KAFKA_CLIENT_INTRO
        + "".join(kafka_client_content)
    )
    cluster_page = (
        CLUSTER_PAGE_TITLE
        + CLUSTER_CONFIG_INTRO
        + CLUSTER_CONFIG_TITLE
        + "".join(cluster_config_content)
    )
    cloud_page = (
        CLOUD_PAGE_TITLE
        + CLOUD_CONFIG_INTRO
        + CLOUD_CONFIG_TITLE
        + "".join(cloud_config_content)
    )
    deprecated_page = (
        DEPRECATED_PROPERTIES_TITLE
        + DEPRECATED_PROPERTIES_INTRO
        + DEPRECATED_BROKER_TITLE
        + "".join(deprecated_broker_content)
        + DEPRECATED_CLUSTER_TITLE
        + "".join(deprecated_cluster_content)
    )

    # Write output files.
    write_data_to_file(page_folder, OUTPUT_FILE_BROKER, broker_page)
    write_data_to_file(page_folder, OUTPUT_FILE_CLUSTER, cluster_page)
    write_data_to_file(page_folder, OUTPUT_FILE_CLOUD, cloud_page)
    write_data_to_file(page_folder, OUTPUT_FILE_DEPRECATED, deprecated_page)
    write_data_to_file(output_dir, ALL_PROPERTIES_FILE, "\n".join(all_properties))

    # Write error files.
    write_error_file(
        error_folder, ERROR_FILE_DESCRIPTION, "\n".join(empty_description_errors), total_properties
    )
    write_error_file(
        error_folder, ERROR_FILE_TYPE, "\n".join(empty_type_errors), total_properties
    )
    write_error_file(
        error_folder, ERROR_FILE_MAX_WITHOUT_MIN, "\n".join(max_without_min_errors), total_properties
    )
    write_error_file(
        error_folder, ERROR_FILE_MIN_WITHOUT_MAX, "\n".join(min_without_max_errors), total_properties
    )
    write_error_file(
        error_folder, "deprecated_properties.txt", "\n".join(deprecated_properties_errors), total_properties
    )

    # Print summary.
    print(f"Total properties read: {total_properties}")
    print(f"Total Broker properties: {len(broker_config_content)}")
    print(f"Total Cluster properties: {len(cluster_config_content)}")
    print(f"Total Cloud properties: {len(cloud_config_content)}")

if __name__ == "__main__":
    main()
