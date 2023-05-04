const fs = require('fs');
const glob = require('glob');
const { execSync } = require('child_process');
const os = require('os');
const path = require('path');

function markdownToAsciidoc(markdown) {

  // Write the Markdown content to a temporary file
  const tempMarkdownPath = path.join(os.tmpdir(), 'temp_markdown.md');
  fs.writeFileSync(tempMarkdownPath, markdown, 'utf-8');

  try {
    const command = `kramdoc -o - "${tempMarkdownPath}"`;
    const result = execSync(command, { encoding: 'utf-8' });

    fs.unlinkSync(tempMarkdownPath); // Remove the temporary Markdown file
    return result;
  } catch (err) {
    fs.unlinkSync(tempMarkdownPath); // Remove the temporary Markdown file
    console.error(`Error converting Markdown to AsciiDoc: ${err.message}`);
    return markdown;
  }
}

function processTabs(match) {
  const tabItems = [...match.matchAll(/<TabItem[^>]*value="([^"]+)"[^>]*label="([^"]+)"[^>]*>([\s\S]*?)<\/TabItem>/g)];

  let result = ['\n\n[tabs]'];
  result.push('=====');
  for (const tabItem of tabItems) {
    const [_, value, label, content] = tabItem;
    result.push(`${label}::`);
    result.push('+');
    result.push('--');
    const asciidocContent = markdownToAsciidoc(content.trim().replace(/\+{2,}/g, ''));
    result.push(asciidocContent);
    result.push('--');
  }

  result.push('=====');
  return result.join('\n');
}

function convertFile(file) {
  const content = fs.readFileSync(file, 'utf-8');

  // Replace Docusaurus tabs with Asciidoctor tabs
  const newContent = content
    .replace(/\+\+\+<Tabs>/g, '<Tabs>') // Remove +++ before <Tabs>
    .replace(/<\/Tabs>\+\+\+/g, '</Tabs>') // Remove +++ after </Tabs>
    .replace(/<Tabs>([\s\S]*?)<\/Tabs>/g, processTabs)
    .replace(/^\+\+\+\s*/gm, '');

  fs.writeFileSync(file, newContent, 'utf-8');
}

function main() {
  if (process.argv.length < 3) {
    console.log('Usage: node convert_docusaurus_tabs.js <directory1> [<directory2> ...]');
    return;
  }

  const directories = process.argv.slice(2);

  for (const directory of directories) {
    console.log(`Processing directory: ${directory}`);

    // Find all Asciidoc files in the directory
    const files = glob.sync(`${directory}/**/*.adoc`, { nodir: true });

    // Convert tabs in each file
    for (const file of files) {
      console.log(`  Converting tabs in: ${file}`);
      convertFile(file);
    }
  }

  console.log('Done.');
}

main();
