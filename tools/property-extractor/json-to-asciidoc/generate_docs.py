import json
import os
import re

input_json_path = "gen/"
input_json_file = "properties-output.json"

output_path = "output/"
page_folder = output_path+"pages/"
output_file_broker = "broker-properties.adoc"
output_file_cluster = "cluster-properties.adoc"
output_file_cloud = "object-storage-properties.adoc"
output_file_deprecated ="deprecated/partials/deprecated-properties.adoc"

error_folder = output_path + "error/"
error_file_description = "empty_description.txt"
error_file_type = "empty_type.txt"
error_file_max_without_min = "max_without_min.txt"
error_file_min_without_max = "min_without_max.txt"


all_properties_file = "all_properties.txt"
all_properties=""
all_properties_count = 0

file_deprecated_properties_error ="deprecated_properties.txt"
deprecated_properties_error =""

empty_description = ""
empty_type = ""
empty_visibility = ""
max_without_min = ""
min_without_max = ""

broker_page_title = "= Broker Configuration Properties \n:page-aliases: reference:node-properties.adoc, reference:node-configuration-sample.adoc\n:description: Reference of broker configuration properties. \n\n"
broker_intro = "Broker configuration properties are applied individually to each broker in a cluster. You can find and modify these properties in the `redpanda.yaml` configuration file.\n\nFor information on how to edit broker properties, see xref:manage:cluster-maintenance/node-property-configuration.adoc[].\n\nNOTE: All broker properties require that you restart Redpanda for any update to take effect.\n\n"
broker_title = "== Broker configuration\n\n"

schema_registry_title = "== Schema Registry\n\n"
pandaproxy_title = "== HTTP Proxy\n\n"
kafka_client_title = "== HTTP Proxy Client\n\n"

schema_registry_intro = "The Schema Registry provides configuration properties to help you enable producers and consumers to share  information needed to serialize and deserialize producer and consumer messages.\n\nFor information on how to edit broker properties for the Schema Registry, see xref:manage:cluster-maintenance/node-property-configuration.adoc[].\n\n"
pandaproxy_intro = "Redpanda HTTP Proxy allows access to your data through a REST API. For example, you can list topics or brokers, get events, produce events, subscribe to events from topics using consumer groups, and commit offsets for a consumer.\n\nSee xref:develop:http-proxy.adoc[]\n\n"
kafka_client_intro = "Configuration options for HTTP Proxy Client.\n\n"

cluster_page_title = "= Cluster Configuration Properties \n:page-aliases: reference:tunable-properties.adoc, reference:cluster-properties.adoc\n:description: Cluster configuration properties list. \n\n"
cluster_config_intro = "Cluster configuration properties are the same for all brokers in a cluster, and are set at the cluster level.\n\nFor information on how to edit cluster properties, see xref:manage:cluster-maintenance/cluster-property-configuration.adoc[] or xref:manage:kubernetes/k-cluster-property-configuration.adoc[].\n\nNOTE: Some cluster properties require that you restart the cluster for any updates to take effect. See the specific property details to identify whether or not a restart is required.\n\n"
cluster_config_title = "== Cluster configuration\n\n"

cloud_page_title = "= Object Storage Properties \n:description: Reference of object storage properties.\n\n"
cloud_config_intro = "Object storage properties are a type of cluster property. For information on how to edit cluster properties, see xref:manage:cluster-maintenance/cluster-property-configuration.adoc[].\n\nNOTE: Some object storage properties require that you restart the cluster for any updates to take effect. See the specific property details to identify whether or not a restart is required.\n\n"
cloud_config_title = "== Object storage configuration\n\nObject storage properties should only be set if you enable xref:manage:tiered-storage.adoc[Tiered Storage].\n\n"

deprecated_properties_title = "\n== Configuration properties\n\n"
deprecated_properties_intro = "This is an exhaustive list of all the deprecated properties.\n\n"
deprecated_broker_title = "=== Broker properties\n\n"
deprecated_cluster_title = "=== Cluster properties\n\n"
deprecated_properties_table = "|===\n| Feature | Deprecated in | Details\n\n"


broker_properties = ""
schema_registry_properties = ""
pandaproxy_properties = ""
kafka_client_properties = ""
cluster_config_properties =  ""
cloud_config_properties =  ""

deprecated_broker_properties =  ""
deprecated_cluster_properties =  ""


yaml_config_start = "[,yaml]\n----\n"
yaml_config_end = "----"
total_properties =0
total_broker_properties=0
total_cluster_properties=0
total_cloud_properties=0

def load_json(input_json_path, input_json_file):
    try:
        with open(os.path.join(input_json_path, input_json_file), 'r') as json_file:
            data = json.load(json_file)
            return data
    except FileNotFoundError:
        print(f"Error: The file '{input_json_file}' does not exist.")
    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse JSON in '{input_json_file}': {str(e)}")

def process_defaults(input_string, suffix):

    # Test for ip:port in vector 
    vector_match = re.search(r'std::vector<net::unresolved_address>\(\{\{("([\d.]+)",\s*(\d+))\}\}\)', input_string)
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
    time_match = re.search(r'(\d+)(ms|s|min|h)', input_string)
    
    # Handle complex time expressions like '24h*365'
    complex_match = re.search(r'(\d+)(h|min|s|ms)\s*\*\s*(\d+)', input_string)

    # Handle std::chrono::time expressions
    chrono_match = re.search(r'std::chrono::(\w+)[\{\(](\d+)[\)\}]', input_string)
    
    if time_match:
        value = int(time_match.group(1))
        unit = time_match.group(2)
        
        # Convert based on suffix and time unit
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
        
        # Handle complex time expressions
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
        
        # Map chrono units to suffix-based conversions
        chrono_conversion = {
            "milliseconds": 1,
            "seconds": 1000,
            "minutes": 60 * 1000,
            "hours": 60 * 60 * 1000,
            "days": 24 * 60 * 60 * 1000,
            "weeks": 7 * 24 * 60 * 60 * 1000
        }

        # Convert based on suffix and chrono unit
        if suffix == "ms":
            return chrono_value * chrono_conversion.get(chrono_unit, 1)
        elif suffix == "sec":
            if chrono_unit == "milliseconds":
                return chrono_value / 1000
            else:
                return chrono_value * chrono_conversion.get(chrono_unit, 1) / 1000

    return default
    
data = load_json(input_json_path, input_json_file)

properties = data.get("properties")
total_properties = len(properties)
if properties is not None:
    # Write each property on a separate line
    for key, value in properties.items():
        output_property=""

        # Grouping
        defined_in_mapping = {
            "src/v/config/node_config.cc": "broker",
            "src/v/pandaproxy/schema_registry/configuration.cc": "schema reg",
            "src/v/pandaproxy/rest/configuration.cc": "http proxy",
            "src/v/kafka/client/configuration.cc": "http client",
            "src/v/config/configuration.cc": "cluster"
        }

        if key.startswith("cloud_"):
            group = "cloud"
        else:
            group = defined_in_mapping.get(value.get("defined_in"), None)

        if (value.get("is_deprecated") is True):
            deprecated_properties_error+=key+"\n"
            if group == "broker":
                deprecated_broker_properties+="- "+key+"\n\n"
            elif group =="cluster":
                deprecated_cluster_properties+="- "+key+"\n\n"
            continue

        description = value.get("description")
        property_suffix = value.get('name').split('_')[-1]
        type = value.get("type")
        visibility = value.get("visibility")
        if description is None or description =='':
            empty_description+=key+"\n"
        if type is None or type =='':
            empty_type+=key+"\n"
        if visibility is None or visibility =='':
            visibility = "user"
        if any(field is None or field == "" for field in [description, key, type]):
            continue

        #have max but dont have min    
        if (value.get("maximum")) is not None:
            if(value.get("minimum")) is None:
                max_without_min+=key+"\n"
        #have max but dont have min  
        if (value.get("minimum")) is not None:
            if(value.get("maximum")) is None:
                min_without_max+=key+"\n"

        #force first capital
        description = description[0].upper() + description[1:]
        if not description.endswith('.'):
            description += '.'
        output_property += (f"=== {value.get('name')}\n\n")
        output_property += description + "\n\n"
        # Suffix mapping
        suffix_to_unit = {
            "ms": "milliseconds",
            "sec": "seconds", #code is not always consistent when using seconds
            "seconds": "seconds",
            "bytes": "bytes",
            "buf": "bytes",
            "partitions": "number of partitions per topic",
            "percent": "percent",
            "bps": "bytes per second",
            "fraction": "fraction"
        }

        units = suffix_to_unit.get(property_suffix)
        if units:
            output_property += f"*Unit:* {units}\n\n"
        #all node_config require restart, regardless of original data
        if group !="broker":
            output_property += "*Requires restart:* " + ("Yes" if value.get("needs_restart", False) else "No") + "\n\n"
        ## Removed as requested output_property += "*Nullable:* " + ("Yes" if nullable else "No") + "\n\n"
        if visibility is not None:
            output_property += "*Visibility:* " + "`%s`" % visibility + "\n\n"
        #exclude complex types for now
        if type  in ["string", "array", "number", "boolean", "integer"]:
            output_property += "*Type:* " + type + "\n\n"
        if value.get('maximum') is not None and value.get('minimum') is not None:
            output_property += "*Accepted values:* " + "[`%d`, `%d`]\n\n" % (value.get("minimum"), value.get("maximum"))
        default = value.get("default")
        if default is None or default =='':
            default = "null"
        elif isinstance(default, bool):
            default =  "true" if default else "false"
        else:
            default = str(default)
            default = default.replace("'", "").lower()
            default = process_defaults(default,property_suffix)
            
            
        output_property += "*Default:* `%s`\n\n" % default
        ## Line separator 
        output_property += "---\n\n"

                # Define a dictionary to map groups to property variables and their respective totals
        properties_mapping = {
            "cloud": {"properties": "cloud_config_properties", "total": "total_cloud_properties"},
            "broker": {"properties": "broker_properties", "total": "total_broker_properties"},
            "schema reg": {"properties": "schema_registry_properties", "total": "total_broker_properties"},
            "http proxy": {"properties": "pandaproxy_properties", "total": "total_broker_properties"},
            "http client": {"properties": "kafka_client_properties", "total": "total_broker_properties"},
            "cluster": {"properties": "cluster_config_properties", "total": "total_cluster_properties"}
        }

        # Assign output property to the correct group
        if group in properties_mapping:
            vars()[properties_mapping[group]["properties"]] += output_property
            vars()[properties_mapping[group]["total"]] += 1

        # Always update all properties
        all_properties += key + '\n'
        all_properties_count += 1

broker_page = broker_page_title + broker_intro + broker_title + broker_properties +"\n\n" 
broker_page +=schema_registry_title + schema_registry_intro + schema_registry_properties+"\n\n"
broker_page +=pandaproxy_title + pandaproxy_intro + pandaproxy_properties+"\n\n"
broker_page +=kafka_client_title + kafka_client_intro + kafka_client_properties

cluster_page = cluster_page_title + cluster_config_intro + cluster_config_title + cluster_config_properties
cloud_page = cloud_page_title + cloud_config_intro + cloud_config_title + cloud_config_properties

deprecated_page = deprecated_properties_title + deprecated_properties_intro
deprecated_page += deprecated_broker_title + deprecated_broker_properties
deprecated_page += deprecated_cluster_title + deprecated_cluster_properties


def write_data_to_file(output_path, output_file, data):
    try:
        with open(os.path.join(output_path, output_file), "w+") as output:
            output.write(data)
    except Exception as e:
        print(f"Error: Failed to write data to {output_file}: {str(e)}")
        return False
    else:
        print(f"Data from {input_json_file} has been written to {output_file} successfully.")
        return True
    
def write_error_file(output_path, error_file, error_content):
    file_path = os.path.join(output_path, error_file)
    try:
        # Delete the existing file if it exists
        if os.path.exists(file_path):
            os.remove(file_path)
        # Write a new file if error_content is not None
        if error_content is not None and error_content != '':
            if error_content.endswith('\n'):
                error_content = error_content[:-1]
            with open(file_path, "w+") as output:
                output.write(error_content)
                error_count = len(error_content.split('\n'))
                if error_count > 0:
                    empty_name = error_file.replace("empty_", "").replace(".txt", "")
                    error_percentage = round((error_count / total_properties) * 100, 2)
                    error_type = "deprecated properties" if empty_name == "deprecated_properties" else f"properties with empty {empty_name}"

                    print(f"You have {error_count} {error_type}. Percentage of errors {error_percentage}%. Data written in '{error_file}'.")

    except Exception as e:
        print(f"Error: Failed to write data to '{error_file}': {str(e)}")

print(f"Total properties read {total_properties}")
print(f"Total Broker properties read {total_broker_properties}")
print(f"Total Cluster properties read {total_cluster_properties}")
print(f"Total Cloud properties read {total_cloud_properties}")


write_data_to_file(page_folder, output_file_broker, broker_page)
write_data_to_file(page_folder, output_file_cluster, cluster_page)
write_data_to_file(page_folder, output_file_cloud, cloud_page)
write_data_to_file(page_folder, output_file_deprecated, deprecated_page)    

write_data_to_file(output_path, all_properties_file, all_properties)

write_error_file(error_folder,error_file_description,empty_description)
write_error_file(error_folder,error_file_type,empty_type)
write_error_file(error_folder,error_file_max_without_min,max_without_min)
write_error_file(error_folder,error_file_min_without_max,min_without_max)
write_error_file(error_folder,file_deprecated_properties_error,deprecated_properties_error)
