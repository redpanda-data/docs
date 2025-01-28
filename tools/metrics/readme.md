# Redpanda Public Metrics Extractor

This automation spins up the enterprise quickstart Docker Compose to create a Redpanda environment, then extracts Redpanda’s public metrics (the `HELP` text) from the `public_metrics` endpoint and stores them as JSON and AsciiDoc files.

## How it works

1. Starts a 3-broker Redpanda cluster using the Docker Compose from the Redpanda quickstart.
2. Fetches metrics from the brokers (`:19644/public_metrics`) and parses out the `# HELP` lines, creating:
   - `metrics.json`
   - `metrics.adoc`

These output files are stored in a versioned folder under `docs/gen/<version>/metrics`, based on the tag you provide or the largest existing version folder if you use `latest`.

## Prerequisites

- **Docker** & **Docker Compose** installed and running.
- **Python 3** & **pip** on your system.

## Usage

1. Change into the `docs/tools/metrics/` directory.

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
   ./extract_metrics.sh [TAG]
   ```

TAG is an optional Redpanda image version (e.g., 24.3.1).

If you omit TAG or pass latest, the script pulls the latest Redpanda Docker image, then looks for the largest version folder inside docs/gen to store the extracted metrics.

## Examples

### No tags

```bash
./extract_metrics.sh
```

This spins up Redpanda with the latest tag, then stores metrics under docs/gen/<largest_found_version>/metrics/.

### Custom tag

```bash
./extract_metrics.sh 24.3.3
```

Docker uses 24.3.3 for the Redpanda image.
The script truncates the last digit (24.3.3 → 24.3) for output folder naming.
Metrics are stored in docs/gen/24.3/metrics.

## Clean Up

When you’re done, you can remove the Docker containers and volumes:

```bash
docker compose down --volumes
```

Or rerun `./extract_metrics.sh` to reset and recreate the environment.

## Caveats

This automation assumes extraction for GA versions of Redpanda. If you wish to extract metrics for unreleased versions of Redpanda, modify the docker-compose.yml from:

```yaml
image: "docker.redpanda.com/redpandadata/redpanda:${REDPANDA_VERSION:-latest}"
```

to:

```yaml
image: "docker.redpanda.com/redpandadata/redpanda-unstable:${REDPANDA_VERSION:-latest}"
```

Check which version you want to use at [Docker Hub - Unstable](https://hub.docker.com/r/redpandadata/redpanda-unstable/tags).

or:

```yaml
image: "docker.redpanda.com/redpandadata/redpanda-nightly:${REDPANDA_VERSION:-latest}"
```

Check which version you want to use at [Docker Hub - Nightly](https://hub.docker.com/r/redpandadata/redpanda-nightly/tags).