const axios = require('axios');

const REDPANDA_DATA_API_URL = 'https://artifacthub.io/api/v1/packages/helm/redpanda-data/redpanda';
const REDPANDA_HELM_CHART_REFERENCE = 'https://artifacthub.io/packages/helm/redpanda-data/redpanda';
// Earliest supported version of Redpanda
const MIN_RP_VERSION = process.argv[2] || '22.3';
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
  const allChartVersions = await fetchAllChartVersions();
  let appVersionsMap = new Map();
  for (const chartVersion of allChartVersions) {
    const chartDetails = await fetchChartDetails(chartVersion);
    if (chartDetails) {
      const majorMinor = convertToMajorMinorVersion(chartDetails.appVersion);
      appVersionsMap.set(majorMinor, chartDetails.appVersion);
    }
  }
  let table = '|===\n| Redpanda Helm Chart |Supported Redpanda Versions|Minimum Kubernetes Version|Minimum Helm Version\n\n';

  for (const chartVersion of allChartVersions) {
    const chartDetails = await fetchChartDetails(chartVersion);
    if (chartDetails && MATRIX_TO_GENERATE === 'redpanda') {
      // Update the map with the current app version
      const majorMinor = convertToMajorMinorVersion(chartDetails.appVersion);

      // Get the three relevant versions
      const supportedVersions = getThreeSupportedVersions(majorMinor, appVersionsMap);

      table += `| link:${REDPANDA_HELM_CHART_REFERENCE}/${chartDetails.chartVersion}[${chartDetails.chartVersion}]\n`;
      table += `| ${supportedVersions.join(', ')}\n`;
      table += `| ${chartDetails.kubernetesVersion}\n`;
      table += `| ${chartDetails.helmVersion}\n\n`;
    } else if (chartDetails && chartDetails.consoleChartVersions && MATRIX_TO_GENERATE === 'console') {

      table += `| link:${REDPANDA_HELM_CHART_REFERENCE}/${chartDetails.chartVersion}[${chartDetails.chartVersion}]\n`;
      table += `| ${chartDetails.consoleChartVersions}\n\n`;

    }
  }

  table += '|===\n';
  console.log(table);
}

async function fetchChartDetails(chartVersion) {
  try {
    const url = `${REDPANDA_DATA_API_URL}/${chartVersion}`;
    const response = await axios.get(url);
    const appVersion = response.data.app_version.replace(/^v/, '');
    if (appVersion === 'latest' || !versionIsGreaterOrEqual(appVersion, MIN_RP_VERSION)) {
      return null;
    }

    let helmVersionMatch;
    let kubeVersionMatch
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
      }
    }

    // Get the Kubernetes version
    if (response.data.data.kubeVersion) {
      const kubeVersionRegex = /^\^?([0-9]+\.[0-9]+(?:\.[0-9]+)?(?:-[0-9]+)?)$/;
      kubeVersionMatch = response.data.data.kubeVersion.match(kubeVersionRegex);
    }

    return {
      chartVersion,
      consoleChartVersions,
      appVersion,
      kubernetesVersion: kubeVersionMatch ?
      kubeVersionMatch[1] :
      '{supported-kubernetes-version}',
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


