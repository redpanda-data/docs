// Import the version fetcher module
const GetLatestRedpandaVersion = require('../../../node_modules/@redpanda-data/docs-extensions-and-macros/extensions/version-fetcher/get-latest-redpanda-version.js');
const yaml = require('../../../node_modules/js-yaml/index.js');
const fs = require('fs');

if (process.argv.length > 3) {
  const overrideDockerRepo = process.argv[2];
  const overrideVersion = process.argv[3];
  console.log(`REDPANDA_DOCKER_REPO=${overrideDockerRepo}`);
  console.log(`REDPANDA_VERSION=${overrideVersion}`);
  process.exit(0);
}

// Fetch the latest release version from GitHub
const owner = 'redpanda-data';
function getPrereleaseFromAntora() {
  try {
    const fileContents = fs.readFileSync('../../antora.yml', 'utf8');
    const antoraConfig = yaml.load(fileContents);
    return antoraConfig.prerelease === true;
  } catch (error) {
    console.error("Error reading antora.yml:", error);
    return false;
  }
}

// Set beta based on the prerelease field in antora.yml or fallback to environment variable
const beta = getPrereleaseFromAntora()
// Conditionally set DOCKER_REPO for subsequent test steps such as the Docker Compose file
if (beta) {
  REDPANDA_DOCKER_REPO = 'redpanda-unstable';
} else {
  REDPANDA_DOCKER_REPO = 'redpanda';
}
const repo = 'redpanda';

async function loadOctokit() {
  const { Octokit } = await import('@octokit/rest');
  if (!process.env.REDPANDA_GITHUB_TOKEN) {
    return new Octokit();
  }
  return new Octokit({
    auth: process.env.REDPANDA_GITHUB_TOKEN,
  });
}

(async () => {
  try {
    const github = await loadOctokit();
    const results = await Promise.allSettled([
      GetLatestRedpandaVersion(github, owner, repo),
    ]);

    const LatestRedpandaVersion = results[0].status === 'fulfilled' ? results[0].value : null;

    if (!LatestRedpandaVersion) {
      throw new Error('Failed to fetch the latest Redpanda version');
    }
    // Determine the release version based on the beta flag, with a fallback to stable release if RC is null
    const latestRedpandaReleaseVersion = beta
      ? (LatestRedpandaVersion.latestRcRelease && LatestRedpandaVersion.latestRcRelease.version
      ? LatestRedpandaVersion.latestRcRelease.version
      : `${LatestRedpandaVersion.latestRedpandaRelease.version}`)
    : `${LatestRedpandaVersion.latestRedpandaRelease.version}`;

    if (!LatestRedpandaVersion.latestRcRelease) REDPANDA_DOCKER_REPO = 'redpanda'

    // Print both version and Docker repo for Doc Detective to capture
    console.log(`REDPANDA_VERSION=${latestRedpandaReleaseVersion}`);
    console.log(`REDPANDA_DOCKER_REPO=${REDPANDA_DOCKER_REPO}`);
  } catch (error) {
    console.error(error);
    process.exit(1);
  }
})();
