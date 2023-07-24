#!/bin/bash

if ! command -v pandoc &> /dev/null; then
  echo "Error: Pandoc is not installed."
  echo "Please visit https://pandoc.org/installing.html to install Pandoc."
  exit 1
fi

SOURCE_DIRECTORY="$1"

if [ -z "$SOURCE_DIRECTORY" ]; then
  echo "Error: Source directory not provided."
  echo "Usage: ./your_script.sh /path/to/your/source_directory"
  exit 1
fi

OUTPUT_DIRECTORY="../modules"

# Create the output and partials directories if they don't exist
mkdir -p "$OUTPUT_DIRECTORY"

function remove_leading_tabs() {
  local mdx_file="$1"
  local content="$(cat "$mdx_file")"

  # Remove leading tabs in the <Tabs> elements
  local updated_content="$(echo "$content" | perl -0777 -pe 's/(\s*)<TabItem([\s\S]*?)>([\s\S]*?)<\/TabItem>/sprintf("%s<TabItem%s>%s<\/TabItem>", $1, $2, $3 =~ s!^\t!!rmsg)/ge')"

  # Write the updated content back to the file
  echo "$updated_content" > "$mdx_file"
}

function preprocess_markdown() {
  local markdown_file="$1"
  node pre-process-markdown.js "$markdown_file"
}

# Convert a Markdown file to AsciiDoc and add the description
function convert_markdown_to_asciidoc() {
  local markdown_file="$1"
  local output_file="$2"
  # Remove leading tabs from <Tab> elements
  remove_leading_tabs "$markdown_file"

  # Preprocess the markdown file
  preprocess_markdown "$markdown_file"

  local content="$(cat "$markdown_file")"

  local output_file_dir="$(dirname "$output_file")"
  mkdir -p "$output_file_dir"

  # Extract the content of the meta description tag
  local description="$(echo "$content" | sed -n 's/.*<meta name="description" content="\([^"]*\)".*/\1/p')"

  # Remove the head element from the source Markdown file and save it
  local cleaned_content="$(echo "$content" | sed '/<head>/,/<\/head>/d')"
  local cleaned_file="$(mktemp)"
  echo "$cleaned_content" > "$cleaned_file"

  # Convert the cleaned Markdown file to AsciiDoc using Kramdoc
  local asciidoc_content="$(kramdoc -o - "$cleaned_file")"

  # Insert the description attribute on the second line of the AsciiDoc content
  asciidoc_content="$(echo "$asciidoc_content" | awk -v desc="$description" 'NR==1{print; print ":description: " desc ""; next} 1')"

  # Write the updated AsciiDoc content to the output file
  echo "$asciidoc_content" > "$output_file"

  echo "Converted: $markdown_file -> $output_file"
}

# Convert all Markdown files in the source directory
while IFS= read -r -d '' markdown_file; do
  output_file="$(echo "$markdown_file" | sed "s|$SOURCE_DIRECTORY|$OUTPUT_DIRECTORY|" | sed 's|\.mdx$|.adoc|' | sed 's|\(.*\)/\(.*\)|\1/pages/\2|')"
  convert_markdown_to_asciidoc "$markdown_file" "$output_file"
  # Run the Node.js script to process the output file
  node post-process-asciidoc.js "$output_file"
done < <(find "$SOURCE_DIRECTORY" -name "*.mdx" -print0)

echo "All Markdown files converted to AsciiDoc."
