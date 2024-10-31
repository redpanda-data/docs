const owner = 'redpanda-data';
const repo = 'console';
const CONSOLE_DOCKER_REPO = 'console'

// Import the version fetcher module
const GetLatestConsoleVersion = require('../../node_modules/@redpanda-data/docs-extensions-and-macros/extensions/version-fetcher/get-latest-console-version.js');

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

    let latestConsoleReleaseVersion;
    /* Avoid fetching Console beta for now until we have a better way to determine the image to use
    if (beta) {
      // If beta, fetch the latest Docker tag by date from console-unstable
      latestConsoleReleaseVersion = await fetchLatestDockerTagByDate(CONSOLE_DOCKER_REPO);
      if (!latestConsoleReleaseVersion) {
        throw new Error(`No valid Docker tags found for ${CONSOLE_DOCKER_REPO}`);
      }
    } else {
      const results = await Promise.allSettled([
        GetLatestConsoleVersion(github, owner, repo),
      ]);
      const LatestConsoleVersion = results[0].status === 'fulfilled' ? results[0].value : null;
      if (!LatestConsoleVersion) {
        throw new Error('Failed to fetch the latest Redpanda version');
      }
      latestConsoleReleaseVersion = `v${LatestConsoleVersion.latestRelease.version}`;
    }*/

    const results = await Promise.allSettled([
      GetLatestConsoleVersion(github, owner, repo),
    ]);
    const LatestConsoleVersion = results[0].status === 'fulfilled' ? results[0].value : null;
    if (!LatestConsoleVersion) {
      throw new Error('Failed to fetch the latest Redpanda version');
    }
    latestConsoleReleaseVersion = `${LatestConsoleVersion}`;

    // Print both version and Docker repo for Doc Detective to capture
    console.log(`CONSOLE_VERSION=${latestConsoleReleaseVersion}`);
    console.log(`CONSOLE_DOCKER_REPO=${CONSOLE_DOCKER_REPO}`);
  } catch (error) {
    console.error(error);
    process.exit(1);
  }
})();

// Fetch Docker tags by date
async function fetchLatestDockerTagByDate(repo) {
  const axios = require('axios'); // Axios to make HTTP requests

  try {
    const response = await axios.get(`https://registry.hub.docker.com/v2/repositories/redpandadata/${repo}/tags`);
    const tags = response.data.results;

    // Find the latest tag by the last updated date
    const latestTag = tags.reduce((latest, tag) => {
      return new Date(tag.last_updated) > new Date(latest.last_updated) ? tag : latest;
    });

    return latestTag.name;
  } catch (error) {
    console.error('Failed to fetch Docker tags:', error);
    return null;
  }
}