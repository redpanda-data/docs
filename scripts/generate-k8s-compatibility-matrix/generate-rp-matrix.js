const axios = require('axios');

const REDPANDA_DATA_API_URL = 'https://artifacthub.io/api/v1/packages/helm/redpanda-data/redpanda';
const REDPANDA_HELM_CHART_REFERENCE = 'https://artifacthub.io/packages/helm/redpanda-data/redpanda';
// Earliest supported version of Redpanda
const MIN_RP_VERSION = process.argv[2] || '22.3';

async function main() {
  try {
    await generateTable();
  } catch (error) {
    console.error('An error occurred:', error.message);
    process.exit(1);
  }
}

main();

async function fetchChartDetails(chartVersion) {
  try {
    const url = `${REDPANDA_DATA_API_URL}/${chartVersion}`;
    const response = await axios.get(url);
    const appVersion = response.data.app_version.replace(/^v/, '');
    if (appVersion === 'latest' || !versionIsGreaterOrEqual(appVersion, MIN_RP_VERSION)) {
      return null;
    }

    // Check the links array for the Helm version
    if (response.data.links) {
      const helmLink = response.data.links.find(link => link.name && link.name.startsWith('Helm (>='));
      if (helmLink) {
        helmVersionMatch = helmLink.name.match(/Helm \(>= ([0-9.]+)\)/);
      }
    }

    const kubernetesVersion = '{supported-kubernetes-version}'
    return {
      chartVersion,
      appVersion,
      kubernetesVersion: kubernetesVersion,
      helmVersion: helmVersionMatch ? helmVersionMatch[1] : '{supported-helm-version}'
    };
  } catch (error) {
    console.error(`Error fetching details for chart ${chartVersion}:`, error.message);
    return null;
  }
}

async function fetchAllChartVersions() {
  try {
    const response = await axios.get(REDPANDA_DATA_API_URL);
    return response.data.available_versions
      .map(v => v.version)
      .filter(v => v !== 'latest');
  } catch (error) {
    console.error('Error fetching Redpanda chart versions:', error.message);
    return [];
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

function majorMinorVersion(version) {
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

async function generateTable() {
  const allChartVersions = await fetchAllChartVersions();
  let appVersionsMap = new Map();
  // Populate appVersionsMap
  for (const chartVersion of allChartVersions) {
    const chartDetails = await fetchChartDetails(chartVersion);
    if (chartDetails) {
      const majorMinor = majorMinorVersion(chartDetails.appVersion);
      appVersionsMap.set(majorMinor, chartDetails.appVersion);
    }
  }
  let table = '|===\n| Redpanda Helm Chart |Supported Redpanda Versions|Minimum Kubernetes Version|Minimum Helm Version\n\n';

  for (const chartVersion of allChartVersions) {
    const chartDetails = await fetchChartDetails(chartVersion);
    if (chartDetails) {
      // Update the map with the current app version
      const majorMinor = majorMinorVersion(chartDetails.appVersion);
      if (!appVersionsMap.has(majorMinor)) {
        appVersionsMap.set(majorMinor, chartDetails.appVersion);
      }

      // Get the three relevant versions
      const supportedVersions = getThreeSupportedVersions(majorMinor, appVersionsMap);

      table += `| link:${REDPANDA_HELM_CHART_REFERENCE}/${chartDetails.chartVersion}[${chartDetails.chartVersion}]\n`;
      table += `| ${supportedVersions.join(', ')}\n`;
      table += `| ${chartDetails.kubernetesVersion}\n`;
      table += `| ${chartDetails.helmVersion}\n\n`;
    }
  }

  table += '|===\n';
  console.log(table);
}

function getThreeSupportedVersions(currentVersion, appVersionsMap) {
  // Sort the versions in descending order
  const sortedVersions = Array.from(appVersionsMap.keys()).sort((a, b) => -compareVersions(a, b));

  const currentIndex = sortedVersions.indexOf(currentVersion);

  const supportedVersions = [];

  // Add the current version and up to two previous versions
  for (let i = currentIndex; i < sortedVersions.length && supportedVersions.length < 3; i++) {
    if (appVersionsMap.has(sortedVersions[i])) {
      supportedVersions.push(sortedVersions[i]);
    }
  }
  return supportedVersions;
}


