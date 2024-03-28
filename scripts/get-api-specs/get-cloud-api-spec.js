const { Octokit } = require("@octokit/rest");
const { retry } = require("@octokit/plugin-retry");
const yaml = require('js-yaml');
const OctokitWithRetries = Octokit.plugin(retry);
const fs = require('fs');

const owner = 'redpanda-data';
const repo = 'cloudv2';
const path = 'proto/gen/openapi/openapi.prod.yaml';

let githubOptions = {
  userAgent: 'Redpanda Docs',
  baseUrl: 'https://api.github.com',
};

if (process.env.VBOT_GITHUB_API_TOKEN) {
  githubOptions.auth = process.env.VBOT_GITHUB_API_TOKEN;
} else {
  console.error('GitHub API token is not set in environment variables');
  process.exit(1);
}

const octokit = new OctokitWithRetries(githubOptions);

async function fetchYamlFile() {
  try {
    const response = await octokit.repos.getContent({
      owner,
      repo,
      path
    });

    const content = Buffer.from(response.data.content, 'base64').toString();

    console.log(content);
  } catch (error) {
    console.error('Error fetching file: ' + error.message);
    process.exit(1)
  }
}

fetchYamlFile();
