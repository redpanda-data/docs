#!/bin/bash

SOURCE_DIRECTORY="./test2"
OUTPUT_DIRECTORY="./asciidoc_docs2/modules"

# Create the output and partials directories if they don't exist
mkdir -p "$OUTPUT_DIRECTORY"

# Convert a Markdown file to AsciiDoc and add the description
function convert_markdown_to_asciidoc() {
  local markdown_file="$1"
  local output_file="$2"
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
  output_file="$(echo "$markdown_file" | sed "s|$SOURCE_DIRECTORY|$OUTPUT_DIRECTORY|" | sed 's|\.mdx$|.adoc|')"
  convert_markdown_to_asciidoc "$markdown_file" "$output_file"
done < <(find "$SOURCE_DIRECTORY" -name "*.mdx" -print0)

echo "All Markdown files converted to AsciiDoc."
