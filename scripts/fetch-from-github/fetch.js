const fs = require('fs');
const path = require('path');

// Function to load Octokit once
let octokitInstance = null;

async function loadOctokit() {
  if (!octokitInstance) {
    const { Octokit } = await import('@octokit/rest');
    octokitInstance = process.env.VBOT_GITHUB_API_TOKEN
      ? new Octokit({
          auth: process.env.VBOT_GITHUB_API_TOKEN,
        })
      : new Octokit();
  }
  return octokitInstance;
}

function logMessage(message, level = 'log') {
  if (level === 'error') {
    console.error(message);
  } else {
    console.log(message);
  }
}

const args = process.argv.slice(2);

function printHelp() {
  logMessage(`
Usage: node script.js <owner> <repo> <path> <save-directory> [custom-filename]

Arguments:
  <owner>           The GitHub repository owner or organization.
  <repo>            The GitHub repository name.
  <path>            The file or directory path within the repository to fetch.
  <save-directory>  The local directory where files will be saved.
  [custom-filename] Optional. If provided, the fetched file will be saved with this name.

Options:
  -h, --help        Show this help message.

Example:
  node fetch.js redpanda-data cloudv2 proto/gen/openapi/openapi.prod.yaml ./modules/ROOT/attachments cloud-api.yaml

Note: Ensure that you have set the 'VBOT_GITHUB_API_TOKEN' environment variable for authentication.
  `);
}

if (args.includes('--help') || args.includes('-h')) {
  printHelp();
  process.exit(0);
}

if (args.length < 4) {
  logMessage('Error: Missing arguments.', 'error');
  printHelp();
  process.exit(1);
}

const [owner, repo, filePath, saveDir, customFilename] = args;

// Create the save directory if it doesn't exist
if (!fs.existsSync(saveDir)) {
  fs.mkdirSync(saveDir, { recursive: true });
}

async function saveFile(content, filename) {
  const filePath = path.join(saveDir, filename);
  fs.writeFileSync(filePath, content);
  logMessage(`Saved: ${filePath}`);
}

async function fetchFile(owner, repo, filePath) {
  const octokit = await loadOctokit();
  try {
    const response = await octokit.repos.getContent({
      owner,
      repo,
      path: filePath,
    });

    if (Array.isArray(response.data)) {
      // Path is a directory, fetch each file in the directory
      for (const file of response.data) {
        if (file.type === 'file') {
          await fetchFile(owner, repo, file.path);
        }
      }
    } else {
      // Path is a file, save its content
      const content = Buffer.from(response.data.content, 'base64').toString();
      // Use custom filename if provided, else use the default one from the repo
      const filename = customFilename || path.basename(response.data.path);
      await saveFile(content, filename);
    }
  } catch (error) {
    logMessage('Error fetching file or directory: ' + error.message, 'error');
    process.exit(1);
  }
}

fetchFile(owner, repo, filePath);
