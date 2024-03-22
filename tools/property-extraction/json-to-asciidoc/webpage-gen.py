import json
import os

input_json_path = "gen/"
input_json_file = "properties-output.json"

output_path = "output/pages/"
output_file_broker = "broker-properties.adoc"
output_file_cluster = "cluster-properties.adoc"
output_file_cloud = "cloud-properties.adoc"
output_file_deprecated ="deprecated/index.adoc"

error_folder = "output/error"
error_file_description = "empty_description.txt"
error_file_nullable = "empty_nullable.txt"
error_file_type = "empty_type.txt"
error_file_visibility = "empty_visibility.txt"
error_file_max_without_min = "max_without_min.txt"
error_file_min_without_max = "min_without_max.txt"

file_deprecated_properties_error ="deprecated_properties.txt"
deprecated_properties_error =""

empty_description = ""
empty_nullable = ""
empty_type = ""
empty_visibility = ""
max_without_min = ""
min_without_max = ""

broker_page_title = "= Broker Configuration Properties \n:description: Broker configuration properties list. \n\n"
broker_intro = "Broker configuration properties are applied individually to each broker in a cluster.\n\nBroker properties can be found and modified at the `redpanda.yaml` configuration file.\n\nFor information on how to edit broker properties, see xref:manage:cluster-maintenance/node-property-configuration.adoc[].\n\n"
broker_title = "== Broker\n\n"

schema_registry_title = "== Schema Registry\n\n"
pandaproxy_title = "== HTTP Proxy\n\n" 
kafka_client_title = "== HTTP Proxy Client\n\n"

schema_registry_intro = "Schema Registry intro\n\n"
pandaproxy_intro = "HTTP Proxy intro\n\n" 
kafka_client_intro = "Kafka Client intro\n\n"

cluster_page_title = "= Cluster Configuration Properties \n:description: Cluster configuration properties list. \n\n"
cluster_config_intro = "Cluster configuration properties are the same for all brokers in a cluster. They can be set at the cluster level.\n\nFor information on how to edit cluster properties, see xref:manage:cluster-maintenance/cluster-property-configuration.adoc[]. Some properties require the cluster to be restarted in order to be applied; see a specific property's reference for whether restart is required.\n\n"
cluster_config_title = "== Cluster Configuration\n\n"

cloud_page_title = "= Cloud Configuration Properties \n:description: Cloud configuration properties list. \n\n"
cloud_config_intro = "Cloud properties intro\n\n"
cloud_config_title = "== Cloud\n\n"

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

try:
    with open(os.path.join(input_json_path, input_json_file), 'r') as json_file:
        data = json.load(json_file)
except FileNotFoundError:
    print(f"Error: The file '{input_json_file}' does not exist.")
    exit(1)
except json.JSONDecodeError as e:
    print(f"Error: Failed to parse JSON in '{input_json_file}': {str(e)}")
    exit(1)

properties = data.get("properties")
total_properties = len(properties)
if properties is not None:
    # Write each property on a separate line
    for key, value in properties.items():
        output_property=""
        if (value.get("is_deprecated") is True):
            deprecated_properties_error+=key+"\n"
            if value.get("defined_in") == "src/v/config/node_config.cc":
                deprecated_broker_properties+="- "+key+"\n\n"
            elif value.get("defined_in") == "src/v/config/configuration.cc":
                deprecated_cluster_properties+="- "+key+"\n\n"
            continue

        description = value.get("description")
        nullable = value.get("nullable")
        type = value.get("type")
        visibility = value.get("visibility")
        if description is None or description =='':
            empty_description+=key+"\n"
        if nullable is None or nullable == '':
            empty_nullable+=key+"\n"
        if type is None or type =='':
            empty_type+=key+"\n"
        if visibility is None or visibility =='':
            empty_visibility+=key+"\n"
            visibility = "None"
        if any(field is None or field == "" for field in [description, key, nullable, type]):
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

        output_property += (f"=== {key}\n\n")
        output_property += description + "\n\n"
        #all node_config require restart, regardless of original data
        if value.get("defined_in") == "src/v/config/node_config.cc":
            output_property += "*Requires Restart:* " +"Yes" +"\n\n"
        else:
            output_property += "*Requires Restart:* " + ("Yes" if value.get("needs_restart", False) else "No") + "\n\n"
        output_property += "*Nullable:* " + ("Yes" if nullable else "No") + "\n\n"
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
        output_property += "*Default:* `%s`\n\n" % default
        ## Line separator 
        output_property += "---\n\n"

        # hard todo
        #output_property += "*Example:* "+ "\n\n"

        #Grouping
        if key.startswith("cloud_"):
            cloud_config_properties+=output_property
            total_cloud_properties+=1
        elif value.get("defined_in") == "src/v/config/node_config.cc":
            broker_properties+=output_property
            total_broker_properties+=1  
        elif value.get("defined_in") == "src/v/pandaproxy/schema_registry/configuration.cc":
            schema_registry_properties+=output_property 
            total_broker_properties+=1
        elif value.get("defined_in") == "src/v/pandaproxy/rest/configuration.cc":
            pandaproxy_properties+=output_property  
            total_broker_properties+=1
        elif value.get("defined_in") == "src/v/kafka/client/configuration.cc":
            kafka_client_properties+=output_property  
            total_broker_properties+=1
        elif value.get("defined_in") == "src/v/config/configuration.cc":
            cluster_config_properties+=output_property
            total_cluster_properties+=1



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
                    print(f"You have {error_count} properties with empty {empty_name}. Percentage of errors {error_percentage}%. Data written in '{error_file}'.")
    except Exception as e:
        print(f"Error: Failed to write data to '{error_file}': {str(e)}")

def write_data_to_file_end(output_path, output_file, data):
    try:
        with open(os.path.join(output_path, output_file), "a") as output:
            output.write(data)
    except Exception as e:
        print(f"Error: Failed to write data to {output_file}: {str(e)}")
        return False
    else:
        print(f"Data has been appended to {output_file} successfully.")
        return True

print(f"Total properties read {total_properties}")
print(f"Total Broker properties read {total_broker_properties}")
print(f"Total Cluster properties read {total_cluster_properties}")
print(f"Total Cloud properties read {total_cloud_properties}")

write_data_to_file(output_path, output_file_broker, broker_page)
write_data_to_file(output_path, output_file_cluster, cluster_page)
write_data_to_file(output_path, output_file_cloud, cloud_page)

write_data_to_file_end(output_path, output_file_deprecated, deprecated_page)    

write_error_file(error_folder,error_file_description,empty_description)
write_error_file(error_folder,error_file_nullable,empty_nullable)
write_error_file(error_folder,error_file_type,empty_type)
write_error_file(error_folder,error_file_visibility,empty_visibility)
write_error_file(error_folder,error_file_max_without_min,max_without_min)
write_error_file(error_folder,error_file_min_without_max,min_without_max)
write_error_file(error_folder,file_deprecated_properties_error,deprecated_properties_error)
