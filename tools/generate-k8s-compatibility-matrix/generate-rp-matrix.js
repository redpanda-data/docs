const axios = require('axios');

const REDPANDA_DATA_API_URL = 'https://artifacthub.io/api/v1/packages/helm/redpanda-data';
const REDPANDA_HELM_CHART_REFERENCE = `${REDPANDA_DATA_API_URL}/redpanda`;
const CONSOLE_HELM_CHART_REFERENCE = `${REDPANDA_DATA_API_URL}/console`;
const OPERATOR_HELM_CHART_REFERENCE = `${REDPANDA_DATA_API_URL}/operator`;
const ARTIFACT_HUB_API_KEY_ID = process.env.ARTIFACT_HUB_API_KEY_ID;
const ARTIFACT_HUB_API_KEY_SECRET = process.env.ARTIFACT_HUB_API_KEY_SECRET;

// User input:
// Earliest supported version of Redpanda.
// Users can pass this into the script as the first argument.
// We display only charts that support later versions of Redpanda.
const MIN_RP_VERSION = process.argv[2] || '22.3';
// Which matrix to generate. Can be redpanda, console, or operator.
const MATRIX_TO_GENERATE = process.argv[3] || 'redpanda';

main();

async function main() {
  try {
    await generateTable();
  } catch (error) {
    console.error('An error occurred:', error.message);
    process.exit(1);
  }
}

async function generateTable() {
  const allRedpandaChartVersions = await fetchAllChartVersions(REDPANDA_HELM_CHART_REFERENCE);
  const allConsoleChartVersions = await fetchAllChartVersions(CONSOLE_HELM_CHART_REFERENCE);
  const allOperatorChartVersions = await fetchAllChartVersions(OPERATOR_HELM_CHART_REFERENCE);

  let table;

  if (MATRIX_TO_GENERATE === 'redpanda') table = '|===\n| Redpanda Helm Chart |Supported Redpanda Versions|Minimum Kubernetes Version|Minimum Helm Version\n\n';
  if (MATRIX_TO_GENERATE === 'console')  table = '|===\n| Redpanda Helm Chart |Default Redpanda Console Chart|Redpanda Console Version\n\n';
  if (MATRIX_TO_GENERATE === 'operator')  table = '|===\n| Redpanda Operator Helm Chart | Redpanda Operator|CRD|Supported Redpanda Helm chart\n\n';

  const processedChartVersions = new Set();

  let supportedRedpandaVersions = new Map();
  for (const chartVersion of allRedpandaChartVersions) {
    const chartDetails = await fetchRedpandaChartDetails(chartVersion);
    if (chartDetails) {
      const appMajorMinor = convertToMajorMinorVersion(chartDetails.appVersion);
      supportedRedpandaVersions.set(appMajorMinor, chartDetails.appVersion);
    }
  }

  for (const chartVersion of allRedpandaChartVersions) {
    const chartMajorMinor = convertToMajorMinorVersion(chartVersion);
    if (!processedChartVersions.has(chartMajorMinor)) {
      const chartDetails = await fetchRedpandaChartDetails(chartVersion);
      if (chartDetails && MATRIX_TO_GENERATE === 'redpanda') {
        const appMajorMinor = convertToMajorMinorVersion(chartDetails.appVersion);

        // Redpanda always has three supported versions available.
        // Calculate which versions are supported by the Redpanda Helm chart,
        // based on the current app version (n - 2).
        const supportedVersions = getThreeSupportedVersions(appMajorMinor, supportedRedpandaVersions);

        table += `| link:https://artifacthub.io/packages/helm/redpanda-data/redpanda/${chartDetails.chartVersion}[${chartMajorMinor}]\n`;
        table += `| ${supportedVersions.join(', ')}\n`;
        table += `| ${chartDetails.kubernetesVersion}\n`;
        table += `| ${chartDetails.helmVersion}\n\n`;

        processedChartVersions.add(chartMajorMinor);

      } else if (chartDetails && chartDetails.consoleChartVersions && MATRIX_TO_GENERATE === 'console') {

        await fetchLatestConsoleChartVersion(chartDetails.consoleChartVersions, allConsoleChartVersions)
          .then(({ latestVersion, appVersion }) => {
            table += `| link:https://github.com/redpanda-data/helm-charts/releases/redpanda-${chartDetails.chartVersion}[${chartMajorMinor}]\n`;
            table += `| link:https://github.com/redpanda-data/helm-charts/releases/console-${latestVersion}[${latestVersion}]\n`;
            table += `| link:https://github.com/redpanda-data/console/releases/v${appVersion}[${appVersion}]\n\n`;
          })
          .catch(error => {
            console.error('Error fetching console chart version:', error.message);
          });

        processedChartVersions.add(chartMajorMinor);
      }
    }
  }

  if (MATRIX_TO_GENERATE === 'operator') {
    // Fetch the latest n-2 versions of the Redpanda Helm chart.
    // Redpanda Operator supports these versions.
    const supportedRedpandaCharts = getLatestThreeMajorMinorVersions(allRedpandaChartVersions);
    for (const chartVersion of allOperatorChartVersions) {
      const chartMajorMinor = convertToMajorMinorVersion(chartVersion);
      if (!processedChartVersions.has(chartMajorMinor)) {
        const chartDetails = await fetchOperatorChartDetails(chartVersion);
        if (!chartDetails.crd) continue
        const appMajorMinor = convertToMajorMinorVersion(chartDetails.appVersion);
        table += `| link:https://github.com/redpanda-data/helm-charts/releases/operator-${chartDetails.chartVersion}[${chartMajorMinor}]\n`;
        table += `| link:https://github.com/redpanda-data/redpanda-operator/releases[${appMajorMinor}]\n`;
        table += `|${chartDetails.crd}\n`;
        table += `|${supportedRedpandaCharts.join(', ')}\n\n`;

        processedChartVersions.add(chartMajorMinor);
      }
    }
  }

  table += '|===\n';
  console.log(table);
}

function getLatestThreeMajorMinorVersions(chartVersions) {
  return chartVersions
    .map(convertToMajorMinorVersion)
    .filter((value, index, self) => self.indexOf(value) === index)
    .sort((a, b) => -compareVersions(a, b))
    .slice(0, 3);
}

// Assuming consoleChartVersions is a string like ">=0.5 <1.0"
async function fetchLatestConsoleChartVersion(consoleChartVersions, allConsoleChartVersions) {
    const versionRange = parseVersionRange(consoleChartVersions);
    const filteredVersions = filterVersionsInRange(allConsoleChartVersions, versionRange);
    const latestVersion = getLatestVersion(filteredVersions);
    const appVersion = await fetchAppVersionForChart(latestVersion);
    return { latestVersion, appVersion };
}

function parseVersionRange(rangeStr) {
    const matches = rangeStr.match(/>=([0-9.]+) <([0-9.]+)/);
    return { minVersion: matches[1], maxVersion: matches[2] };
}

function filterVersionsInRange(versions, range) {
    return versions.filter(version =>
      compareVersions(version, range.minVersion) >= 0 &&
      compareVersions(version, range.maxVersion) < 0);
}

function getLatestVersion(versions) {
    return versions[0];
}

async function fetchAppVersionForChart(chartVersion) {
  const url = `${CONSOLE_HELM_CHART_REFERENCE}/${chartVersion}`
  const response = await fetchWithExponentialBackoff(url)
  return response.data.app_version.replace(/^v/, '');
}

async function fetchOperatorChartDetails(chartVersion) {
  try {
    const url = `${OPERATOR_HELM_CHART_REFERENCE}/${chartVersion}`;
    const response = await fetchWithExponentialBackoff(url)
    const appVersion = response.data.app_version.replace(/^v/, '');
    let crdVersions = ''

    const crds = response.data.crds;
    if (crds) {
      for (i = 0; i < crds.length; i++) {
        crdVersions += `\n\nxref:reference:k-crd-index.adoc[${crds[i].kind} ${crds[i].version}]`
      }
    }

    return {
      chartVersion,
      appVersion,
      crd: crdVersions
    };
  } catch (error) {
    console.error(`Error fetching details for chart ${chartVersion}:`, error.message);
    process.exit(1)
  }
}

async function fetchRedpandaChartDetails(chartVersion) {
  try {
    const url = `${REDPANDA_HELM_CHART_REFERENCE}/${chartVersion}`;
    const response = await fetchWithExponentialBackoff(url)
    const appVersion = response.data.app_version.replace(/^v/, '');
    if (appVersion === 'latest' || !versionIsGreaterOrEqual(appVersion, MIN_RP_VERSION)) {
      return null;
    }

    let kubernetesVersion;
    let helmVersion;
    let consoleChartVersions;

    const deps = response.data.data.dependencies;
    if (deps) {
      for (i = 0; i < deps.length; i++) {
        if (deps[i].name !== 'console') continue
        consoleChartVersions = deps[i].version
      }
    }

    // Check the links array for the Helm version
    if (response.data.links) {
      const helmLink = response.data.links.find(link => link.name && link.name.startsWith('Helm (>='));
      if (helmLink) {
        helmVersionMatch = helmLink.name.match(/Helm \(>= ([0-9.]+)\)/);
        helmVersion = helmVersionMatch ? helmVersionMatch[1] : '3.6.0'
      }
    }

    // Get the Kubernetes version defined in the chart metadata
    if (response.data.data.kubeVersion) {
      const kubeVersionRegex = /^\^?([0-9]+\.[0-9]+(?:\.[0-9]+)?(?:-[0-9]+)?)$/;
      let kubeVersionMatch = response.data.data.kubeVersion.match(kubeVersionRegex);
      kubernetesVersion = kubeVersionMatch ? kubeVersionMatch[1] : '{supported-kubernetes-version}';
    }

    return {
      chartVersion,
      consoleChartVersions,
      appVersion,
      kubernetesVersion,
      helmVersion
    };
  } catch (error) {
    console.error(`Error fetching details for chart ${chartVersion}:`, error.message);
    process.exit(1)
  }
}

async function fetchWithExponentialBackoff(url, retries = 5, delay = 1000) {
  try {
    const response = await axios.get(url, {
      headers: {
        'X-API-KEY-ID': ARTIFACT_HUB_API_KEY_ID,
        'X-API-KEY-SECRET': ARTIFACT_HUB_API_KEY_SECRET
      }
    });
    return response;
  } catch (error) {
    if (retries === 0 || error.response.status !== 429) throw error;

    console.log(`Rate limit exceeded. Retrying in ${delay}ms...`);
    await new Promise(resolve => setTimeout(resolve, delay));
    return fetchWithExponentialBackoff(url, retries - 1, delay * 2);
  }
}

async function fetchAllChartVersions(chart) {
  try {
    const response = await fetchWithExponentialBackoff(chart)
    return response.data.available_versions
      .filter(item => item.prerelease === false)
      .map(v => v.version)
      .filter(v => v !== 'latest');
  } catch (error) {
    console.error('Error fetching chart versions:', error.message);
    process.exit(1)
  }
}

function versionIsGreaterOrEqual(version, minVersion) {
  const versionParts = version.split('.').map(Number);
  const minVersionParts = minVersion.split('.').map(Number);
  for (let i = 0; i < Math.min(versionParts.length, minVersionParts.length); i++) {
    if (versionParts[i] > minVersionParts[i]) return true;
    if (versionParts[i] < minVersionParts[i]) return false;
  }
  return versionParts.length >= minVersionParts.length;
}

function convertToMajorMinorVersion(version) {
  return version.split('.').slice(0, 2).join('.') + '.x';
}

function compareVersions(v1, v2) {
  const parts1 = v1.split('.').map(Number);
  const parts2 = v2.split('.').map(Number);

  for (let i = 0; i < 2; i++) {
    if (parts1[i] > parts2[i]) return 1;
    if (parts1[i] < parts2[i]) return -1;
  }
  return 0;
}

function getThreeSupportedVersions(currentVersion, supportedRedpandaVersions) {
  const sortedVersions = Array.from(supportedRedpandaVersions.keys()).sort((a, b) => -compareVersions(a, b));
  const currentIndex = sortedVersions.indexOf(currentVersion);
  const supportedVersions = [];

  for (let i = currentIndex; i < sortedVersions.length && supportedVersions.length < 3; i++) {
    if (supportedRedpandaVersions.has(sortedVersions[i])) {
      supportedVersions.push(`link:https://github.com/redpanda-data/redpanda/releases/[${sortedVersions[i]}]`);
    }
  }
  return supportedVersions;
}
