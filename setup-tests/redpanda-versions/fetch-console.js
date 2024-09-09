const semver = require("semver");
const owner = 'redpanda-data';
const repo = 'console';

async function loadOctokit() {
  const { Octokit } = await import('@octokit/rest');
  if (!process.env.REDPANDA_GITHUB_TOKEN) return new Octokit()
  return new Octokit({
    auth: process.env.REDPANDA_GITHUB_TOKEN,
  });
}

(async () => {
  try {
    const github = await loadOctokit();
    // Fetch the latest 10 releases
    const releases = await github.rest.repos.listReleases({
      owner,
      repo,
      per_page: 10,
    });

    // Filter valid semver tags and sort them
    const sortedReleases = releases.data
      .map(release => release.tag_name.replace(/^v/, ''))
      .filter(tag => semver.valid(tag))
      // Sort in descending order to get the highest version first
      .sort(semver.rcompare);

    if (sortedReleases.length > 0) {
      console.log(sortedReleases[0]);
    } else {
      console.log("No valid semver releases found.");
      process.exit(1)
    }
  } catch (error) {
    console.error(error);
    process.exit(1)
  }
})()