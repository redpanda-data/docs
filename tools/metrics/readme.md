# Redpanda Metrics Extractor

This automation extracts Redpanda’s public and internal metrics (the `HELP` text) from the `public_metrics/` and `metrics/` endpoints and stores them as JSON and AsciiDoc files.

## How it works

1. Starts a 3-broker Redpanda cluster using a Docker Compose file.
2. Fetches metrics from the brokers and parses out the `# HELP` lines, creating:
   - `metrics.json`
   - `metrics.adoc`

These output files are stored in a versioned folder under `docs/gen/<version>/metrics`, based on the tag you provide or the largest existing version folder if you use `latest`.

## Prerequisites

- **Docker** & **Docker Compose** installed and running.
- **Python 3** & **pip** on your system.

## Usage

1. Change into the `tools/metrics/` directory.

2. Create a Python virtual environment
   ```bash
   python3 -m venv venv
   ```
   This command creates a new directory named `venv/` in your project root.

3. Activate the virtual environment:

   On macOS/Linux:
   ```bash
   source venv/bin/activate
   ```

   On Windows:
   ```powershell
   venv\Scripts\activate
   ```

   After activation, your terminal prompt will be prefixed with (venv) to indicate the active environment.

4. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

5. Run the script:

   ```bash
   ./extract_metrics.sh [REDPANDA_TAG] [REDPANDA_DOCKER_REPO] [REDPANDA_CONSOLE_TAG]  [REDPANDA_CONSOLE_DOCKER_REPO]
   ```

Parameters

- `REDPANDA_TAG` (Optional): Specifies the version tag for the Redpanda image. Default: `latest`.

- `REDPANDA_DOCKER_REPO` (Optional): Specifies the Docker repository for the Redpanda image.
Default: `redpanda`.

- `REDPANDA_CONSOLE_TAG` (Optional): Specifies the version tag for the Redpanda Console image. Default: `latest`.

- `REDPANDA_CONSOLE_DOCKER_REPO` (Optional): Specifies the Docker repository for the Redpanda Console image. Default: `console`.

## Examples

### No tags

```bash
./extract_metrics.sh
```

This spins up Redpanda with the latest tag, then stores metrics under `docs/gen/<largest_found_version>/metrics/`.

### Custom tag

```bash
./extract_metrics.sh 24.3.3
```

Docker uses 24.3.3 for the Redpanda image.
The script truncates the last digit (24.3.3 → 24.3) for output folder naming.
Metrics are stored in `docs/gen/24.3/metrics`.

## Clean up

When you’re done:

1. Deactivate the Python virtual environment:

   ```bash
   deactivate
   ```

2. Remove the Docker containers and volumes:

   ```bash
   docker compose down --volumes
   ```

## Beta versions

This automation assumes extraction for GA versions of Redpanda. To extract metrics for unreleased versions of Redpanda, set the `REDPANDA_DOCKER_REPO` parameter.

This example runs on the v25.1.1-rc3 version of Redpanda:

```yaml
./extract_metrics.sh v25.1.1-rc3 redpanda-unstable
```

Check which version you want to use at [Docker Hub - Unstable](https://hub.docker.com/r/redpandadata/redpanda-unstable/tags).

For nightly releases use the `redpanda-nightly` repo.

Check which version you want to use at [Docker Hub - Nightly](https://hub.docker.com/r/redpandadata/redpanda-nightly/tags).