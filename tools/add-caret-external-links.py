import os
import re

# Define the regular expression pattern to match the links
pattern = r'(https://[^\]]+)\[([^\]]+)\](?!\^)'

# Function to process a single file
def process_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    def replace_link(match):
        link = match.group(1)
        text = match.group(2)
        if text.endswith('^'):
            return match.group(0)  # No modification if caret is already present
        else:
            return f"{link}[{text}^]"

    lines = content.split('\n')
    updated_lines = []
    for line in lines:
        if re.search(pattern, line):
            line = re.sub(pattern, replace_link, line)
        updated_lines.append(line)

    # Write the updated content back to the file
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write('\n'.join(updated_lines))

# Get the directory of the current script
script_directory = os.path.dirname(os.path.abspath(__file__))

# Construct the directory path for the 'modules' directory
directory_path = os.path.join(script_directory, '..', 'modules')

# List of excluded file paths (relative paths)
exclusion_list = [
    'reference\\pages\\redpanda-operator\\crd.adoc',
    'reference\\pages\\k-console-helm-spec.adoc',
    'reference\\pages\\crd.adoc',
    'reference\\pages\\k-redpanda-helm-spec.adoc',
    'reference\\partials\\bundle-contents-k8s.adoc',
    'reference\\partials\\bundle-contents-linux.adoc'
]

# Function to process all .adoc files in a directory
def process_directory(directory_path):
    for root, _, files in os.walk(directory_path):
        for file in files:
            if file.endswith('.adoc'):
                file_path = os.path.join(root, file)
                relative_file_path = os.path.relpath(file_path, directory_path)
                if relative_file_path not in exclusion_list:
                    process_file(file_path)
                    print(f"Processed: {file_path}")

# Call the function with the constructed directory path
process_directory(directory_path)
