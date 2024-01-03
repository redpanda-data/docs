import json
import yaml
import os

input_json_path = "gen/" 
input_json_file = "broker.json" 

output_path = "../modules/reference/pages/"
output_file = "node-properties2.adoc"

try:
    with open(input_json_path+ input_json_file, "r") as json_file:
        data = json.load(json_file)
except FileNotFoundError:
    print(f"Error: The file '{input_json_file}' does not exist.")
    exit(1)
except json.JSONDecodeError as e:
    print(f"Error: Failed to parse JSON in '{input_json_file}': {str(e)}")
    exit(1)

intro = "= Broker Configuration Properties \n:description: Broker configuration properties list. \n\nBroker configuration properties are applied individually to each broker in a cluster. \n\nIMPORTANT: After you change a broker-level property setting, you must restart the broker for the change to take effect. \n\nTo learn how to set these properties from studying a sample configuration file, see the xref:./node-configuration-sample.adoc[broker configuration sample].\n\n---\n\n"
yaml_config_start ="[,yaml]\n----\n" 
yaml_config_end ="----" 
properties = data.get("properties")
output_content = intro
output_properties =""

if properties is not None:
    # Write each property on a separate line
    for key, value in properties.items():
        output_properties += (f"== {key}\n\n")
        output_properties += value.get("description") + "\n\n"
        output_properties += "*Example:* " + "\n" + yaml_config_start + yaml.dump(value, default_style='"') +yaml_config_end+'\n\n'
        output_properties += "*Nullable:* " + ("Yes" if value.get("nullable") is True else "No") + "\n\n"
        output_properties += "*Requires Restart:* " + ("Yes" if value.get("needs_restart") is True else "No") + "\n\n"
        output_properties += "*Visibility:* " + value.get("visibility") + "\n\n"
        output_properties += "*Is Secret:* " + ("Yes" if value.get("is_secret") is True else "No")  + "\n\n"
        output_properties += "*Type:* " + value.get("type") + "\n\n"
        
try:
    with open(output_path + output_file, "w+") as output:
        output.write(output_content + output_properties)
except Exception as e:
    print(f"Error: Failed to write data to '{output_file}': {str(e)}")
    exit(1)
print(f"Data from '{input_json_file}' has been written to '{output_file}' successfully.")
