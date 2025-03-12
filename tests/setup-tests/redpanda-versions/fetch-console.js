// Import the version fetcher module
const GetLatestConsoleVersion = require('../../../node_modules/@redpanda-data/docs-extensions-and-macros/extensions/version-fetcher/get-latest-console-version.js');
const yaml = require('../../../node_modules/js-yaml/index.js');
const fs = require('fs');

if (process.argv.length > 3) {
  const overrideDockerRepo = process.argv[2];
  const overrideVersion = process.argv[3];
  console.log(`CONSOLE_DOCKER_REPO=${overrideDockerRepo}`);
  console.log(`CONSOLE_VERSION=${overrideVersion}`);
  process.exit(0);
}

const owner = 'redpanda-data';
const repo = 'console';
const CONSOLE_DOCKER_REPO = 'console'

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

// GitHub Octokit initialization
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
      GetLatestConsoleVersion(github, owner, repo),
    ]);
    const LatestConsoleVersion = results[0].status === 'fulfilled' ? results[0].value : null;
    if (!LatestConsoleVersion) {
      throw new Error('Failed to fetch the latest Redpanda version');
    }
    // Determine the release version based on the beta flag, with a fallback to stable release if RC is null
    const latestConsoleReleaseVersion = beta
      ? (LatestConsoleVersion.latestBetaRelease
        ? LatestConsoleVersion.latestBetaRelease
        : `${LatestConsoleVersion.latestStableRelease}`)
      : `${LatestConsoleVersion.latestStableRelease}`;

    // Print both version and Docker repo for Doc Detective to capture
    console.log(`CONSOLE_VERSION=${latestConsoleReleaseVersion}`);
    console.log(`CONSOLE_DOCKER_REPO=${CONSOLE_DOCKER_REPO}`);
  } catch (error) {
    console.error(error);
    process.exit(1);
  }
})();