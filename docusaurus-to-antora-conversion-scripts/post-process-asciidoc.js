const fs = require('fs');
const path = require('path');

function processFile(file) {
  const content = fs.readFileSync(file, 'utf-8');

  const newContent = content.replace(
    /link:(\.\.\/)+([\w/-]+)(#?[\w/-]*)(\[.+?\])/g,
    (match, dots, linkPath, anchor, linkText) => {
      const depth = dots.match(/\.\.\//g).length;
      const pathParts = linkPath.split('/');
      const newPath = pathParts.slice(0, pathParts.length - depth).join(':');
      return `xref:${newPath}:${pathParts[pathParts.length - 1]}.adoc${anchor || ''}${linkText}`;
    }
  );

  fs.writeFileSync(file, newContent, 'utf-8');
}

function processDirectory(directory) {
  const files = fs.readdirSync(directory);

  files.forEach((file) => {
    const filePath = path.join(directory, file);
    const stat = fs.statSync(filePath);

    if (stat.isFile() && path.extname(file) === '.adoc') {
      processFile(filePath);
    } else if (stat.isDirectory()) {
      processDirectory(filePath);
    }
  });
}

const inputPath = process.argv[2];

if (!inputPath) {
  console.error('No input path provided');
  process.exit(1);
}

const stat = fs.statSync(inputPath);

if (stat.isFile()) {
  processFile(inputPath);
} else if (stat.isDirectory()) {
  processDirectory(inputPath);
} else {
  console.error('Input path is neither a file nor a directory');
  process.exit(1);
}
