# DEVPROD-4307 GCP Devcluster — Implementation Plan (Phase 1)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up the GCP devcluster infrastructure and tooling for Oxla up to the manual validation gate (DEVPROD-4314), producing 6 mergeable PRs across two repos.

**Architecture:** Two devprod-infra PRs create the GCP project resources and IAM (WIF pool + service accounts). Four Oxla repo PRs create the Terraform module, userdata/Ansible, build pipeline AR push, and manual deploy script.

**Tech Stack:** Terraform (HCL), Ansible, GitHub Actions YAML, Python 3, Google Cloud (GCE, GCS, AR, IAM, WIF), `gcloud` CLI.

**Prereqs before any PR can be applied:**
- `testing-oxla` GCP project exists ✅, billing linked ✅ (`billingAccounts/0197D7-A02C67-8BD1C4`)
- `tf-devprod-infra@devprod-cicd-infra.iam.gserviceaccount.com` must have `roles/owner` on `testing-oxla` (manual Ivo step — required before PR 1 TF can apply)
- TFC workspace `testing-oxla` created (manual step — required before PR 2 TF can apply)

---

## PR 1 — DEVPROD-4309: WIF + Service Accounts (`devprod-infra/gcp-oidc/`)

### Task 1: Create branch

**Files:**
- Repo: `devprod-infra`

- [ ] **Create branch**
```bash
cd /home/przemo/workspace/devprod-infra
git checkout main && git pull
git checkout -b devprod-4309-oxla-wif-testing-oxla
```

---

### Task 2: Add testing-oxla provider alias and tf-devprod-infra bootstrap grant

**Files:**
- Modify: `gcp-oidc/main.tf`

- [ ] **Add provider alias and tf-devprod-infra owner grant at the top of `gcp-oidc/main.tf` after the existing `provider "google"` block**

Add after the closing `}` of the existing `provider "google"` block:

```hcl
# Provider for resources that must live in the testing-oxla project
provider "google" {
  alias   = "testing_oxla"
  project = "testing-oxla"
  region  = "europe-west4"
  default_labels = {
    redpanda-org = "engineering-devprod-sdlc-cicd"
  }
}

# Allow tf-devprod-infra TFC SA to manage all resources in testing-oxla.
# BOOTSTRAP NOTE: this resource can only apply after Ivo has manually granted
# tf-devprod-infra@devprod-cicd-infra.iam.gserviceaccount.com roles/owner on testing-oxla.
resource "google_project_iam_member" "tf-devprod-infra-testing-oxla" {
  provider = google.testing_oxla
  project  = "testing-oxla"
  role     = "roles/owner"
  member   = "serviceAccount:${module.tf-devprod-infra.service_account_email}"
}
```

---

### Task 3: Add GitHub WIF OIDC provider for the Oxla repo

**Files:**
- Modify: `gcp-oidc/main.tf`

The existing `gh-id-provider` module creates the SA in the default project (`devprod-cicd-infra`). For Oxla we only need the **WIF provider** from that module (not its SA). We inline the provider resource directly.

- [ ] **Add WIF OIDC providers for the Oxla repo (one for CI workflows, one for build) at the end of `gcp-oidc/main.tf`**

```hcl
# ── Oxla / testing-oxla ──────────────────────────────────────────────────────

# OIDC provider for Oxla GitHub Actions workflows (infra + build).
# SA lives in testing-oxla (cross-project WIF binding — supported by GCP).
resource "google_iam_workload_identity_pool_provider" "gh-oxla" {
  workload_identity_pool_id          = split("/", google_iam_workload_identity_pool.cicd.id)[5]
  workload_identity_pool_provider_id = "gh-Oxla"
  description                        = "oidc identity pool provider for github repo Oxla"
  attribute_mapping = {
    "google.subject"                = "'owner:' + assertion.repository_owner + ':repo:' + assertion.repository.split('/')[1]"
    "attribute.actor"               = "assertion.actor"
    "attribute.repository"          = "assertion.repository"
    "attribute.repository_id"       = "assertion.repository_id"
    "attribute.repository_owner"    = "assertion.repository_owner"
    "attribute.repository_owner_id" = "assertion.repository_owner_id"
  }
  attribute_condition = "attribute.repository_owner_id=='49406389'&&google.subject=='owner:redpanda-data:repo:Oxla'"
  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}
```

---

### Task 4: Create the two Oxla service accounts in testing-oxla

**Files:**
- Modify: `gcp-oidc/main.tf`

- [ ] **Append SA resources to `gcp-oidc/main.tf`**

```hcl
# Infra SA — used by Oxla GHA workflows that provision devclusters
resource "google_service_account" "oxla-ci-github" {
  provider     = google.testing_oxla
  account_id   = "oxla-ci-github"
  display_name = "Oxla CI GitHub Actions (infra)"
  description  = "WIF-bound SA for Oxla GHA devcluster workflows"
  project      = "testing-oxla"
}

# Build SA — used by the Oxla build workflow to push images to AR
resource "google_service_account" "oxla-ci-build" {
  provider     = google.testing_oxla
  account_id   = "oxla-ci-build"
  display_name = "Oxla CI Build (AR push)"
  description  = "WIF-bound SA for Oxla image push to Artifact Registry"
  project      = "testing-oxla"
}
```

---

### Task 5: Bind WIF pool subjects to the two SAs

**Files:**
- Modify: `gcp-oidc/main.tf`

- [ ] **Append WIF binding resources to `gcp-oidc/main.tf`**

```hcl
# Bind the Oxla repo GHA token subject to the infra SA in testing-oxla
resource "google_service_account_iam_member" "oxla-ci-github-wif" {
  provider           = google.testing_oxla
  service_account_id = google_service_account.oxla-ci-github.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principal://iam.googleapis.com/${google_iam_workload_identity_pool.cicd.name}/subject/owner:redpanda-data:repo:Oxla"
}

# Same binding for the build SA
resource "google_service_account_iam_member" "oxla-ci-build-wif" {
  provider           = google.testing_oxla
  service_account_id = google_service_account.oxla-ci-build.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principal://iam.googleapis.com/${google_iam_workload_identity_pool.cicd.name}/subject/owner:redpanda-data:repo:Oxla"
}
```

---

### Task 6: Grant IAM roles on testing-oxla to both SAs

**Files:**
- Modify: `gcp-oidc/main.tf`

- [ ] **Append IAM grant resources to `gcp-oidc/main.tf`**

```hcl
# IAM grants for oxla-ci-github on testing-oxla project
# compute.admin is project-scoped; Terraform per-cluster restricts by label managed-by=oxla-ci
locals {
  oxla_ci_github_roles = toset([
    "roles/compute.admin",
    "roles/storage.admin",
    "roles/iam.serviceAccountAdmin",
    "roles/artifactregistry.reader",
    "roles/iam.serviceAccountUser",  # needed to attach per-cluster SAs to GCE instances
  ])
}

resource "google_project_iam_member" "oxla-ci-github" {
  for_each = local.oxla_ci_github_roles
  provider = google.testing_oxla
  project  = "testing-oxla"
  role     = each.value
  member   = "serviceAccount:${google_service_account.oxla-ci-github.email}"
}

# Build SA only needs AR write access
resource "google_project_iam_member" "oxla-ci-build-ar-writer" {
  provider = google.testing_oxla
  project  = "testing-oxla"
  role     = "roles/artifactregistry.writer"
  member   = "serviceAccount:${google_service_account.oxla-ci-build.email}"
}
```

- [ ] **Run `terraform fmt`**
```bash
cd /home/przemo/workspace/devprod-infra/gcp-oidc
terraform fmt main.tf
```

- [ ] **Validate**
```bash
terraform init -backend=false
terraform validate
```
Expected: `Success! The configuration is valid.`

- [ ] **Commit**
```bash
cd /home/przemo/workspace/devprod-infra
git add gcp-oidc/main.tf
git commit -m "gcp-oidc: add Oxla WIF provider and SAs in testing-oxla (DEVPROD-4309)"
```

---

## PR 2 — DEVPROD-4308: Project resources (`devprod-infra/testing-oxla/`)

### Task 7: Scaffold the testing-oxla Terraform workspace

**Files:**
- Create: `testing-oxla/main.tf`
- Create: `testing-oxla/variables.tf`
- Create: `testing-oxla/outputs.tf`

- [ ] **Create the directory**
```bash
mkdir -p /home/przemo/workspace/devprod-infra/testing-oxla
```

- [ ] **Create `testing-oxla/variables.tf`**

```hcl
variable "project_id" {
  description = "GCP project ID"
  type        = string
  default     = "testing-oxla"
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "europe-west4"
}
```

- [ ] **Create `testing-oxla/outputs.tf`**

```hcl
output "vpc_name" {
  value = google_compute_network.vpc.name
}

output "subnet_name" {
  value = google_compute_subnetwork.subnet.name
}

output "terraform_state_bucket" {
  value = google_storage_bucket.terraform_state.name
}

output "blueprint_bucket" {
  value = google_storage_bucket.blueprint.name
}

output "ar_oxla_daily_url" {
  value = "europe-west4-docker.pkg.dev/${var.project_id}/oxla-daily"
}

output "ar_oxla_compilation_url" {
  value = "europe-west4-docker.pkg.dev/${var.project_id}/oxla-compilation"
}
```

---

### Task 8: Write testing-oxla/main.tf — backend, provider, APIs, VPC

**Files:**
- Modify: `testing-oxla/main.tf`

- [ ] **Create `testing-oxla/main.tf` with TFC backend, provider, API enablement, and VPC**

```hcl
terraform {
  cloud {
    organization = "redpanda-data"
    workspaces {
      name = "testing-oxla"
    }
  }
  required_version = ">= 1.10, < 2.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
  default_labels = {
    redpanda-org = "engineering-devprod-sdlc-cicd"
  }
}

# ── APIs ──────────────────────────────────────────────────────────────────────

resource "google_project_service" "apis" {
  for_each = toset([
    "compute.googleapis.com",
    "storage.googleapis.com",
    "iam.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "artifactregistry.googleapis.com",
    "iamcredentials.googleapis.com",
    "sts.googleapis.com",
  ])
  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}

# ── VPC ──────────────────────────────────────────────────────────────────────

resource "google_compute_network" "vpc" {
  name                    = "testing-oxla-vpc"
  auto_create_subnetworks = false
  depends_on              = [google_project_service.apis]
}

resource "google_compute_subnetwork" "subnet" {
  name          = "testing-oxla-subnet"
  ip_cidr_range = "10.0.0.0/16"
  region        = var.region
  network       = google_compute_network.vpc.id
}

# Allow SSH + Oxla + Node Exporter from anywhere (devclusters are ephemeral, public)
resource "google_compute_firewall" "devcluster_external" {
  name    = "testing-oxla-devcluster-external"
  network = google_compute_network.vpc.name

  allow {
    protocol = "tcp"
    ports    = ["22", "5432", "9100"]
  }
  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["oxla-devcluster"]
}

# Allow all internal traffic between cluster nodes and client
resource "google_compute_firewall" "devcluster_internal" {
  name    = "testing-oxla-devcluster-internal"
  network = google_compute_network.vpc.name

  allow { protocol = "tcp" }
  allow { protocol = "udp" }
  allow { protocol = "icmp" }

  source_tags = ["oxla-devcluster"]
  target_tags = ["oxla-devcluster"]
}
```

---

### Task 9: Add GCS buckets and AR repos to testing-oxla/main.tf

**Files:**
- Modify: `testing-oxla/main.tf`

- [ ] **Append GCS buckets to `testing-oxla/main.tf`**

```hcl
# ── GCS Buckets ───────────────────────────────────────────────────────────────

# Terraform state backend for devcluster-gcp runs (each run uploads state as GHA artifact;
# this bucket is available for future non-GHA use)
resource "google_storage_bucket" "terraform_state" {
  name                        = "testing-oxla-terraform-state"
  location                    = var.region
  uniform_bucket_level_access = true
  force_destroy               = false

  versioning { enabled = true }
}

# Blueprint Oxla home — populated by dev_cluster_create_new_home.yml with cloud_provider=gcp
resource "google_storage_bucket" "blueprint" {
  name                        = "oxla-devcluster-home-blueprint-testing-oxla"
  location                    = var.region
  uniform_bucket_level_access = true
  force_destroy               = false

  versioning { enabled = true }
}
```

- [ ] **Append AR Docker repos to `testing-oxla/main.tf`**

```hcl
# ── Artifact Registry Docker repos ────────────────────────────────────────────

resource "google_artifact_registry_repository" "oxla_daily" {
  location      = var.region
  repository_id = "oxla-daily"
  format        = "DOCKER"
  description   = "Oxla daily release images (mirrors ECR oxla-daily)"
  depends_on    = [google_project_service.apis]
}

resource "google_artifact_registry_repository" "oxla_compilation" {
  location      = var.region
  repository_id = "oxla-compilation"
  format        = "DOCKER"
  description   = "Oxla build environment images (mirrors ECR oxla-compilation)"
  depends_on    = [google_project_service.apis]
}
```

- [ ] **Append IAM grants on AR repos to `testing-oxla/main.tf`**

```hcl
# ── AR IAM grants ─────────────────────────────────────────────────────────────

locals {
  ar_repos = {
    daily       = google_artifact_registry_repository.oxla_daily.id
    compilation = google_artifact_registry_repository.oxla_compilation.id
  }
}

# Build SA can push to both repos
resource "google_artifact_registry_repository_iam_member" "build_sa_writer" {
  for_each   = local.ar_repos
  location   = var.region
  repository = each.value
  role       = "roles/artifactregistry.writer"
  member     = "serviceAccount:oxla-ci-build@testing-oxla.iam.gserviceaccount.com"
}

# Infra SA can pull from both repos (per-cluster SAs also need reader — granted at project level by gcp-oidc)
resource "google_artifact_registry_repository_iam_member" "github_sa_reader" {
  for_each   = local.ar_repos
  location   = var.region
  repository = each.value
  role       = "roles/artifactregistry.reader"
  member     = "serviceAccount:oxla-ci-github@testing-oxla.iam.gserviceaccount.com"
}
```

- [ ] **Run `terraform fmt` and validate**
```bash
cd /home/przemo/workspace/devprod-infra/testing-oxla
terraform fmt .
terraform init -backend=false
terraform validate
```
Expected: `Success! The configuration is valid.`

- [ ] **Commit**
```bash
cd /home/przemo/workspace/devprod-infra
git add testing-oxla/
git commit -m "testing-oxla: add VPC, GCS buckets, AR repos (DEVPROD-4308)"
```

> **Submit PRs 1 and 2 now (in this order). Wait for both to be merged and TF applied before continuing to PR 3.**

---

## PR 3 — DEVPROD-4310: Terraform module (`Oxla/terraform/devcluster-gcp/`)

### Task 10: Create branch and scaffold module files

**Files:**
- Repo: `Oxla`

- [ ] **Create branch**
```bash
cd /home/przemo/workspace/Oxla
git fetch origin
git checkout -b devprod-4310-terraform-devcluster-gcp origin/main
mkdir -p terraform/devcluster-gcp/templates
```

---

### Task 11: Write `terraform/devcluster-gcp/providers.tf`

**Files:**
- Create: `terraform/devcluster-gcp/providers.tf`

- [ ] **Create `providers.tf`**

```hcl
terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
  }
}

provider "google" {
  project = var.gcp_project
  region  = var.region
}
```

---

### Task 12: Write `terraform/devcluster-gcp/variables.tf`

**Files:**
- Create: `terraform/devcluster-gcp/variables.tf`

- [ ] **Create `variables.tf`**

```hcl
variable "gcp_project" {
  description = "GCP project ID"
  type        = string
  default     = "testing-oxla"
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "europe-west4"
}

variable "zone" {
  description = "GCP zone within the region"
  type        = string
  default     = "europe-west4-a"
}

variable "devcluster_alias" {
  description = "Short alias for the cluster (e.g. 'dev', 'gha12345')"
  type        = string
  default     = "dev"
}

variable "devcluster_node_count" {
  description = "Number of Oxla nodes"
  type        = number
  default     = 1
  validation {
    condition     = var.devcluster_node_count >= 1 && var.devcluster_node_count <= 10
    error_message = "Node count must be 1–10"
  }
}

variable "devcluster_machine_type" {
  description = "GCE machine type for devcluster nodes (e.g. n2-standard-32, t2a-standard-16)"
  type        = string
  default     = "n2-standard-8"
}

variable "devcluster_architecture" {
  description = "CPU architecture override: 'x86' or 'arm'. Empty = auto-detect from machine type."
  type        = string
  default     = ""
  validation {
    condition     = contains(["", "x86", "arm"], var.devcluster_architecture)
    error_message = "Architecture must be 'x86', 'arm', or empty"
  }
}

variable "client_machine_type" {
  description = "GCE machine type for the test client node"
  type        = string
  default     = "n2-standard-4"
}

variable "network" {
  description = "VPC network name"
  type        = string
  default     = "testing-oxla-vpc"
}

variable "subnetwork" {
  description = "Subnetwork name"
  type        = string
  default     = "testing-oxla-subnet"
}

variable "devcluster_home_name" {
  description = "Oxla home directory name inside the GCS bucket"
  type        = string
  default     = "home"
}

variable "devcluster_bucket_name" {
  description = "Override for the GCS bucket name. Empty = auto-generated."
  type        = string
  default     = ""
}

variable "devcluster_copy_blueprint" {
  description = "Copy blueprint home in userdata during boot"
  type        = bool
  default     = false
}

variable "blueprint_bucket" {
  description = "GCS bucket containing the blueprint Oxla home"
  type        = string
  default     = "oxla-devcluster-home-blueprint-testing-oxla"
}

variable "ar_registry" {
  description = "Artifact Registry hostname"
  type        = string
  default     = "europe-west4-docker.pkg.dev"
}

variable "oxla_password" {
  description = "Oxla password. Empty = auto-generate."
  type        = string
  default     = ""
  sensitive   = true
}

variable "github_deploy_key" {
  description = "GitHub deploy key (SSH private key) injected into the client node for git clone"
  type        = string
  default     = ""
  sensitive   = true
}
```

---

### Task 13: Write `terraform/devcluster-gcp/main.tf`

**Files:**
- Create: `terraform/devcluster-gcp/main.tf`

- [ ] **Create `main.tf`**

```hcl
locals {
  # Architecture detection: t2a-* = ARM, everything else = x86
  detected_architecture = startswith(var.devcluster_machine_type, "t2a-") ? "arm" : "x86"
  architecture          = var.devcluster_architecture != "" ? var.devcluster_architecture : local.detected_architecture

  # Cluster naming: gh-dev-n2-standard-8-1n-dev
  machine_sanitized = replace(replace(var.devcluster_machine_type, "standard-", "std"), "-", "-")
  alias_sanitized   = replace(var.devcluster_alias, "_", "-")
  devcluster_type   = "${replace(var.devcluster_machine_type, ".", "-")}-${var.devcluster_node_count}n"
  devcluster_name   = "gh-dev-${local.devcluster_type}-${local.alias_sanitized}"

  generated_bucket_name = "oxla-gcp-${var.devcluster_node_count}n-${local.alias_sanitized}"
  bucket_name           = var.devcluster_bucket_name != "" ? var.devcluster_bucket_name : local.generated_bucket_name

  oxla_password = var.oxla_password != "" ? var.oxla_password : random_password.oxla_password.result

  devcluster_labels = {
    "devcluster-name" = local.devcluster_name
    "managed-by"      = "oxla-ci"
    "oxla"            = "true"
  }
}

resource "random_password" "oxla_password" {
  length  = 16
  special = false
}

# ── SSH key ───────────────────────────────────────────────────────────────────

resource "tls_private_key" "devcluster_ssh" {
  algorithm = "ED25519"
}

# ── Per-cluster service account ───────────────────────────────────────────────

resource "google_service_account" "devcluster" {
  # SA IDs max 30 chars; use a short derived name
  account_id   = substr("oxla-${local.alias_sanitized}", 0, 28)
  display_name = "Oxla devcluster ${local.devcluster_name}"
  project      = var.gcp_project
}

resource "google_project_iam_member" "devcluster_ar_reader" {
  project = var.gcp_project
  role    = "roles/artifactregistry.reader"
  member  = "serviceAccount:${google_service_account.devcluster.email}"
}

# ── GCS bucket for cluster home ───────────────────────────────────────────────

resource "google_storage_bucket" "devcluster_home" {
  name          = local.bucket_name
  location      = var.region
  project       = var.gcp_project
  force_destroy = true

  uniform_bucket_level_access = true
}

resource "google_storage_bucket_iam_member" "devcluster_home_admin" {
  bucket = google_storage_bucket.devcluster_home.name
  role   = "roles/storage.admin"
  member = "serviceAccount:${google_service_account.devcluster.email}"
}

# Blueprint bucket: read-only access for blueprint copy during userdata
resource "google_storage_bucket_iam_member" "devcluster_blueprint_reader" {
  bucket = var.blueprint_bucket
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.devcluster.email}"
}

# Store SSH private key in GCS for easy retrieval
resource "google_storage_bucket_object" "ssh_private_key" {
  name    = "ssh-keys/id_ed25519"
  bucket  = google_storage_bucket.devcluster_home.name
  content = tls_private_key.devcluster_ssh.private_key_openssh
}

# ── GCE devcluster nodes ──────────────────────────────────────────────────────

resource "google_compute_instance" "devcluster_nodes" {
  count        = var.devcluster_node_count
  name         = "${local.devcluster_name}-node-${count.index + 1}"
  machine_type = var.devcluster_machine_type
  zone         = var.zone
  project      = var.gcp_project
  labels       = local.devcluster_labels
  tags         = ["oxla-devcluster"]

  boot_disk {
    initialize_params {
      image = local.architecture == "arm" ? "ubuntu-os-cloud/ubuntu-2204-lts-arm64" : "ubuntu-os-cloud/ubuntu-2204-lts"
      size  = 256
      type  = "pd-ssd"
    }
  }

  network_interface {
    network    = var.network
    subnetwork = var.subnetwork
    access_config {}  # ephemeral public IP
  }

  service_account {
    email  = google_service_account.devcluster.email
    scopes = ["cloud-platform"]
  }

  metadata = {
    ssh-authorized-keys = "ubuntu:${tls_private_key.devcluster_ssh.public_key_openssh}"
    user-data = base64encode(templatefile("${path.module}/userdata.sh", {
      node_id           = "n${count.index + 1}"
      cluster_name      = local.devcluster_name
      devcluster_bucket = local.bucket_name
      blueprint_bucket  = var.blueprint_bucket
      home_name         = var.devcluster_home_name
      copy_blueprint    = var.devcluster_copy_blueprint
      ar_registry       = var.ar_registry
      gcp_project       = var.gcp_project
      is_client         = false
    }))
  }
}

# ── GCE client node ───────────────────────────────────────────────────────────

resource "google_compute_instance" "client_node" {
  name         = "${local.devcluster_name}-client"
  machine_type = var.client_machine_type
  zone         = var.zone
  project      = var.gcp_project
  labels       = local.devcluster_labels
  tags         = ["oxla-devcluster"]

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2204-lts"
      size  = 50
      type  = "pd-ssd"
    }
  }

  network_interface {
    network    = var.network
    subnetwork = var.subnetwork
    access_config {}
  }

  service_account {
    email  = google_service_account.devcluster.email
    scopes = ["cloud-platform"]
  }

  metadata = {
    ssh-authorized-keys = "ubuntu:${tls_private_key.devcluster_ssh.public_key_openssh}"
    github-deploy-key   = var.github_deploy_key
    user-data = base64encode(templatefile("${path.module}/userdata.sh", {
      node_id           = "client"
      cluster_name      = local.devcluster_name
      devcluster_bucket = local.bucket_name
      blueprint_bucket  = var.blueprint_bucket
      home_name         = var.devcluster_home_name
      copy_blueprint    = false
      ar_registry       = var.ar_registry
      gcp_project       = var.gcp_project
      is_client         = true
    }))
  }
}
```

---

### Task 14: Write `terraform/devcluster-gcp/outputs.tf`

**Files:**
- Create: `terraform/devcluster-gcp/outputs.tf`

- [ ] **Create `outputs.tf`**

```hcl
output "devcluster_name" {
  description = "Full devcluster name"
  value       = local.devcluster_name
}

output "devcluster_architecture" {
  description = "CPU architecture (arm or x86)"
  value       = local.architecture
}

output "devcluster_bucket_name" {
  description = "GCS bucket name for devcluster home"
  value       = google_storage_bucket.devcluster_home.name
}

output "oxla_password" {
  description = "Oxla database password"
  value       = local.oxla_password
  sensitive   = true
}

output "public_ips" {
  description = "Public IPs of devcluster nodes"
  value       = [for inst in google_compute_instance.devcluster_nodes : inst.network_interface[0].access_config[0].nat_ip]
}

output "private_ips" {
  description = "Private IPs of devcluster nodes"
  value       = [for inst in google_compute_instance.devcluster_nodes : inst.network_interface[0].network_ip]
}

output "client_node_public_ip" {
  description = "Public IP of the GCE client node"
  value       = google_compute_instance.client_node.network_interface[0].access_config[0].nat_ip
}

output "client_node_private_ip" {
  description = "Private IP of the GCE client node"
  value       = google_compute_instance.client_node.network_interface[0].network_ip
}

output "ssh_private_key" {
  description = "SSH private key for all cluster nodes"
  value       = tls_private_key.devcluster_ssh.private_key_openssh
  sensitive   = true
}

output "ssh_public_key" {
  value = tls_private_key.devcluster_ssh.public_key_openssh
}

output "ansible_inventory" {
  description = "Ansible inventory YAML (ready to use)"
  sensitive   = true
  value = templatefile("${path.module}/templates/ansible-inventory.yml.tpl", {
    devcluster_name        = replace(local.devcluster_name, "-", "_")
    nodes = [
      for i, inst in google_compute_instance.devcluster_nodes : {
        name       = "n${i + 1}_${replace(local.devcluster_name, "-", "_")}"
        public_ip  = inst.network_interface[0].access_config[0].nat_ip
        private_ip = inst.network_interface[0].network_ip
      }
    ]
    client_name            = "client_${replace(local.devcluster_name, "-", "_")}"
    client_public_ip       = google_compute_instance.client_node.network_interface[0].access_config[0].nat_ip
    client_private_ip      = google_compute_instance.client_node.network_interface[0].network_ip
    ansible_user           = "ubuntu"
    devcluster_name        = local.devcluster_name
    devcluster_bucket_name = local.bucket_name
    oxla_home_name         = var.devcluster_home_name
    oxla_password          = local.oxla_password
    disable_table_tasks    = var.devcluster_copy_blueprint
  })
}
```

---

### Task 15: Write the Ansible inventory template

**Files:**
- Create: `terraform/devcluster-gcp/templates/ansible-inventory.yml.tpl`

- [ ] **Create `templates/ansible-inventory.yml.tpl`**

```yaml
all:
  children:
    ${devcluster_name}:
      hosts:
%{ for node in nodes ~}
        ${node.name}:
          ansible_host: ${node.private_ip}
          public_ip: ${node.public_ip}
          private_ip: ${node.private_ip}
%{ endfor ~}
    client:
      hosts:
        ${client_name}:
          ansible_host: ${client_public_ip}
          public_ip: ${client_public_ip}
          private_ip: ${client_private_ip}
  vars:
    provider: gcp
    ansible_user: ${ansible_user}
    devcluster_name: ${devcluster_name}
    devcluster_bucket_name: ${devcluster_bucket_name}
    oxla_home_name: ${oxla_home_name}
    oxla_password: ${oxla_password}
    disable_table_tasks: ${disable_table_tasks}
```

- [ ] **Run `terraform fmt` and validate**
```bash
cd /home/przemo/workspace/Oxla/terraform/devcluster-gcp
terraform init -backend=false
terraform validate
```
Expected: `Success! The configuration is valid.`

- [ ] **Commit**
```bash
cd /home/przemo/workspace/Oxla
git add terraform/devcluster-gcp/
git commit -m "terraform: add GCP devcluster module (DEVPROD-4310)"
```

---

## PR 4 — DEVPROD-4311 + 4312: userdata.sh + Ansible playbook

> Continue on the same branch (`devprod-4310-terraform-devcluster-gcp`) or open a new one from it.

### Task 16: Write `terraform/devcluster-gcp/userdata.sh`

**Files:**
- Create: `terraform/devcluster-gcp/userdata.sh`

- [ ] **Create `userdata.sh`**

```bash
#!/bin/bash
set -e

echo "=== GCP Devcluster Node Setup ==="
echo "Node ID: ${node_id}"
echo "Cluster name: ${cluster_name}"
echo "Devcluster bucket: ${devcluster_bucket}"
echo "GCP project: ${gcp_project}"
echo "Is client: ${is_client}"

# ── System packages ────────────────────────────────────────────────────────────
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get upgrade -y
apt-get install -y \
  apt-transport-https \
  ca-certificates \
  curl \
  gnupg \
  software-properties-common \
  unzip \
  jq \
  wget

# ── Architecture detection ─────────────────────────────────────────────────────
ARCH=$(uname -m)
if [ "$ARCH" = "x86_64" ]; then
  DOCKER_ARCH="amd64"
elif [ "$ARCH" = "aarch64" ]; then
  DOCKER_ARCH="arm64"
else
  echo "Unsupported architecture: $ARCH"; exit 1
fi
echo "Architecture: $ARCH -> $DOCKER_ARCH"

# ── Docker ────────────────────────────────────────────────────────────────────
mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$DOCKER_ARCH signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
systemctl start docker
systemctl enable docker
usermod -aG docker ubuntu
echo "Docker installed: $(docker --version)"

# ── Google Cloud SDK ──────────────────────────────────────────────────────────
echo "=== Installing Google Cloud SDK ==="
curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg | gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg
echo "deb [arch=$DOCKER_ARCH signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" \
  | tee /etc/apt/sources.list.d/google-cloud-sdk.list > /dev/null
apt-get update
apt-get install -y google-cloud-cli
echo "gcloud installed: $(gcloud --version | head -1)"

# ── Docker credential helper for GCP AR ───────────────────────────────────────
# The attached service account authenticates automatically via the metadata server.
gcloud auth configure-docker ${ar_registry} --quiet

# Also configure for ubuntu user
sudo -u ubuntu gcloud auth configure-docker ${ar_registry} --quiet

echo "Docker configured for AR registry: ${ar_registry}"

# ── Node Exporter ─────────────────────────────────────────────────────────────
NODE_EXPORTER_VERSION="1.7.0"
if [ "$ARCH" = "x86_64" ]; then
  NODE_EXPORTER_ARCH="linux-amd64"
else
  NODE_EXPORTER_ARCH="linux-arm64"
fi
wget -q https://github.com/prometheus/node_exporter/releases/download/v$NODE_EXPORTER_VERSION/node_exporter-$NODE_EXPORTER_VERSION.$NODE_EXPORTER_ARCH.tar.gz
tar -xzf node_exporter-$NODE_EXPORTER_VERSION.$NODE_EXPORTER_ARCH.tar.gz -C /opt
ln -sf /opt/node_exporter-$NODE_EXPORTER_VERSION.$NODE_EXPORTER_ARCH/node_exporter /usr/local/bin/node_exporter
rm node_exporter-$NODE_EXPORTER_VERSION.$NODE_EXPORTER_ARCH.tar.gz
cat > /etc/systemd/system/node_exporter.service <<'EOF'
[Unit]
Description=Node Exporter
After=network.target
[Service]
Type=simple
User=root
ExecStart=/usr/local/bin/node_exporter
[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable node_exporter
systemctl start node_exporter

# ── Kernel core dump ─────────────────────────────────────────────────────────
mkdir -p /oxla/crash
echo "/oxla/crash/%t-core-%e-%p-%h" > /proc/sys/kernel/core_pattern
echo "kernel.core_pattern=/oxla/crash/%t-core-%e-%p-%h" >> /etc/sysctl.conf

%{ if is_client }
# ── Client node extra packages ─────────────────────────────────────────────────
echo "=== Installing client node packages ==="
apt-get install -y python3-pip git postgresql-client
pip3 install --no-cache-dir tox requests==2.31.0 docker==6.1.3

# Install GitHub deploy key if provided via GCE metadata
DEPLOY_KEY=$(curl -sf -H "Metadata-Flavor: Google" \
  http://metadata.google.internal/computeMetadata/v1/instance/attributes/github-deploy-key || true)
if [ -n "$DEPLOY_KEY" ]; then
  mkdir -p /home/ubuntu/.ssh
  echo "$DEPLOY_KEY" > /home/ubuntu/.ssh/id_ed25519
  chmod 600 /home/ubuntu/.ssh/id_ed25519
  chown ubuntu:ubuntu /home/ubuntu/.ssh/id_ed25519
  ssh-keyscan github.com >> /home/ubuntu/.ssh/known_hosts
  chown ubuntu:ubuntu /home/ubuntu/.ssh/known_hosts
  echo "GitHub deploy key installed"
fi
%{ endif }

%{ if copy_blueprint }
if [ "${node_id}" = "n1" ]; then
  echo "=== Copying blueprint Oxla home ==="
  gcloud storage cp -r \
    gs://${blueprint_bucket}/${home_name}/ \
    gs://${devcluster_bucket}/${home_name}/
  echo "Blueprint copy complete"
fi
%{ endif }

echo "=== GCP node setup complete: ${node_id} ==="
```

---

### Task 17: Write `ansible/devcluster_deploy_gcp.yml`

**Files:**
- Create: `ansible/devcluster_deploy_gcp.yml`
- Create: `ansible/templates/config_gcp.yml.j2`

- [ ] **Create `ansible/devcluster_deploy_gcp.yml`**

```yaml
---
# GCP DEVCLUSTER DEPLOYMENT
# Based on devcluster_deploy_aws.yml — cloud-specific differences:
#   - No IMDSv2 credential fetch (GCE service account handles auth automatically)
#   - aws s3 rm  →  gcloud storage rm
#   - aws ecr get-login-password  →  gcloud auth print-access-token
#   - oxla_home_path uses gs:// instead of s3://
#   - [client] inventory group present alongside [oxla_nodes]

- name: Freeze deployments
  tags: [never, freeze]
  hosts: all
  tasks:
    - name: Create freeze file
      ansible.builtin.file:
        path: "{{ ansible_env.HOME }}/oxla/FREEZE"
        state: touch

- name: Stop previous deployment
  tags: [never, stop]
  hosts: "{{ devcluster_name }}"
  any_errors_fatal: true
  tasks:
    - name: Reset SSH connection to pick up docker group membership
      meta: reset_connection
    - name: Force remove deployment freeze
      tags: [never, force]
      ansible.builtin.file:
        path: "{{ ansible_env.HOME }}/oxla/FREEZE"
        state: absent
    - name: Check deployment freeze
      stat:
        path: "{{ ansible_env.HOME }}/oxla/FREEZE"
      register: freeze_stat_result
    - name: Fail due to deployment freeze
      when: freeze_stat_result.stat.exists
      fail:
        msg: "Deployment freeze active"
    - name: Check if compose config exists
      stat:
        path: "{{ ansible_env.HOME }}/oxla/config.yml"
      register: config_stat_result
    - name: Get info for all oxla docker containers
      community.docker.docker_host_info:
        containers: yes
        containers_all: yes
        containers_filters:
          name: ".*oxla.*"
      register: oxla_containers
    - name: Compose down
      when: config_stat_result.stat.exists and oxla_containers.containers | length > 0
      community.docker.docker_compose_v2:
        project_src: "{{ ansible_env.HOME }}/oxla/"
        files:
          - config.yml
        state: absent

- name: Clean home
  hosts: "{{ devcluster_name }}[0]"
  gather_facts: no
  tags: [never, clean_home]
  tasks:
    - name: Remove oxla home files with gcloud
      shell: "gcloud storage rm --recursive gs://{{ devcluster_bucket_name }}/{{ oxla_home_name }}"

- name: Clean shared
  hosts: "{{ devcluster_name }}[0]"
  gather_facts: no
  tags: [never, clean_shared]
  tasks:
    - name: Remove shared files with gcloud
      shell: "gcloud storage rm --recursive gs://{{ devcluster_bucket_name }}/shared"

- name: Authenticate Docker to GCP Artifact Registry
  hosts: "{{ devcluster_name }}"
  gather_facts: no
  tasks:
    - name: Configure docker credential helper for AR
      shell: gcloud auth configure-docker europe-west4-docker.pkg.dev --quiet
      changed_when: false

- name: Setup oxla cluster
  hosts: "{{ devcluster_name }}"
  vars:
    image: "europe-west4-docker.pkg.dev/testing-oxla/oxla-daily:latest"
    postgres_port: 5432
    asio_node_port: 5771
    slots_port: 5770
    prometheus_port: 8080
    leader_name: "{{ hostvars[ansible_play_hosts[0]].ansible_host }}"
    oxla_home_path: "gs://{{ devcluster_bucket_name }}/{{ oxla_home_name }}"
    access_control__mode: DEFAULT
    log_level: "VERBOSE"
    run_on_distributed_catalog: false
    disable_table_tasks: false

  tasks:
    - name: Reset SSH connection to pick up docker group membership
      meta: reset_connection

    - name: Print configuration info
      debug:
        msg: "Config: leader_name={{ leader_name }}, bucket={{ devcluster_bucket_name }}, home={{ oxla_home_path }}, image={{ image }}"

    - name: Check image
      fail:
        msg: "Image cannot be empty"
      when: image | length == 0

    - name: Create deployment directories
      file:
        path: "{{ ansible_env.HOME }}/oxla/{{ item }}"
        state: directory
      loop:
        - ""
        - crash
        - data
        - logs
        - metrics
        - client_data

    - name: Update docker compose config file
      template:
        src: templates/config_gcp.yml.j2
        dest: "{{ ansible_env.HOME }}/oxla/config.yml"

    - name: Compose up
      community.docker.docker_compose_v2:
        project_src: "{{ ansible_env.HOME }}/oxla/"
        files:
          - config.yml
        state: present
        pull: always
        recreate: always

    - name: Dump Oxla leader logs
      shell: |
        docker compose -f {{ ansible_env.HOME }}/oxla/config.yml logs --no-color | tail -n 200 || true
      args:
        chdir: "{{ ansible_env.HOME }}/oxla"
      register: oxla_logs
      changed_when: false

    - name: Print Oxla logs
      debug:
        msg: "{{ oxla_logs.stdout_lines | default([]) }}"
```

- [ ] **Create `ansible/templates/config_gcp.yml.j2`**

```yaml
version: '3.5'

services:
  node:
    image: {{ image }}
    security_opt:
      - seccomp:unconfined
    restart: always
    ulimits:
      nofile:
        soft: 40000
        hard: 40000
    volumes:
      - ./crash:/oxla/crash
      - ./data:/oxla/data
      - ./logs:/oxla/logs
      - ./client_data:/client_data
    ports:
      - {{ postgres_port }}:{{ postgres_port }}
      - {{ slots_port }}:{{ slots_port }}
      - {{ prometheus_port }}:{{ prometheus_port }}
      - {{ asio_node_port }}:{{ asio_node_port }}
    environment:
      # GCS paths — authentication via the GCE instance's attached service account (ADC)
      - SHARED_MEMORY__CLUSTER__PATH=gs://{{ devcluster_bucket_name }}/shared/
      - OXLA_HOME={{ oxla_home_path }}
      - OXLA_LOG_FILE=/oxla/logs/{{ lookup('env', 'GITHUB_RUN_ID') | default(ansible_date_time.epoch, true) }}-{{ lookup('env', 'GITHUB_RUN_ATTEMPT') | default('0', true) }}.log
      - HOST_NAME={{ ansible_host }}
      - LOG_LEVEL={{ log_level }}
      - MEMORY__MAX={{ (ansible_memtotal_mb * 0.8) | round | int }}M
      - ACCESS_CONTROL__MODE={{ access_control__mode }}
      - ACCESS_CONTROL__INITIAL_PASSWORD={{ oxla_password }}
{% if disable_table_tasks | bool %}
      - FEATURE_FLAGS__DISABLE_TABLE_TASKS=true
{% endif %}
      - FEATURE_FLAGS__LOG_AGGR_IN_NO_COL_GROUPBY=true
{% if run_on_distributed_catalog | bool %}
      - FEATURE_FLAGS__DISTRIBUTED_CATALOG_ENABLED=true
      - FORCE_LARGE_INSERTIONS=true
{% endif %}
      - LEADER_ELECTION__LEADER_NAME={{ leader_name }}
      - STORE_COREDUMPS=1
      - FEATURE_FLAGS__ARRAY_SUPPORT=TRUE
```

- [ ] **Commit**
```bash
cd /home/przemo/workspace/Oxla
git add terraform/devcluster-gcp/userdata.sh ansible/devcluster_deploy_gcp.yml ansible/templates/config_gcp.yml.j2
git commit -m "devcluster-gcp: add userdata.sh and Ansible playbook (DEVPROD-4311, DEVPROD-4312)"
```

---

## PR 5 — DEVPROD-4313: Build pipeline → push to GCP AR

### Task 18: Create branch and modify `create_multiarch_image.yml`

**Files:**
- Modify: `.github/workflows/create_multiarch_image.yml`

- [ ] **Create branch**
```bash
cd /home/przemo/workspace/Oxla
git fetch origin
git checkout -b devprod-4313-ar-push origin/main
```

- [ ] **Add `ar_target_image` optional input to `create_multiarch_image.yml`**

In the `on.workflow_call.inputs:` block, add after the `latest:` input:

```yaml
      ar_target_image:
        description: "Optional: push a copy of this manifest to GCP Artifact Registry (e.g. europe-west4-docker.pkg.dev/testing-oxla/oxla-daily:daily-2025-01-01). Leave empty to skip."
        type: string
        default: ""
```

- [ ] **Add GCP auth + AR push steps to `create_multiarch_image.yml`**

In the `jobs.create-multiarch-image.steps:` list, add after the `"Show manifest info"` step:

```yaml
      - name: "Authenticate to GCP for AR push"
        if: inputs.ar_target_image != ''
        uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: "projects/devprod-cicd-infra-NUMBER/locations/global/workloadIdentityPools/rp-cicd/providers/gh-Oxla"
          service_account: "oxla-ci-build@testing-oxla.iam.gserviceaccount.com"
      - name: "Configure Docker for GCP AR"
        if: inputs.ar_target_image != ''
        run: gcloud auth configure-docker europe-west4-docker.pkg.dev --quiet
      - name: "Push manifest to GCP Artifact Registry"
        if: inputs.ar_target_image != ''
        run: |
          docker buildx imagetools create \
            -t ${{ inputs.ar_target_image }} \
            ${{ inputs.x64_image }} \
            ${{ inputs.arm_image }}
          echo "✓ Pushed to AR: ${{ inputs.ar_target_image }}"
```

> **Note:** Replace `devprod-cicd-infra-NUMBER` with the actual project number from `gcloud projects describe devprod-cicd-infra --format="value(projectNumber)"`. This is needed to construct the full WIF provider resource name.

- [ ] **Wire `ar_target_image` in `daily_checks.yml`**

In the `create-multiarch-manifest` job's `with:` block, add:

```yaml
      ar_target_image: ${{ github.event_name != 'workflow_dispatch' && format('europe-west4-docker.pkg.dev/testing-oxla/oxla-daily:daily-$(date +%Y-%m-%d)') || '' }}
```

- [ ] **Commit**
```bash
cd /home/przemo/workspace/Oxla
git add .github/workflows/create_multiarch_image.yml .github/workflows/daily_checks.yml
git commit -m "ci: push oxla-daily images to GCP Artifact Registry (DEVPROD-4313)"
```

---

## PR 6 — DEVPROD-4314: `tools/deploy_devcluster_gcp.py`

### Task 19: Create branch and write the deploy script

**Files:**
- Create: `tools/deploy_devcluster_gcp.py`

- [ ] **Create branch**
```bash
cd /home/przemo/workspace/Oxla
git fetch origin
git checkout -b devprod-4314-deploy-devcluster-gcp origin/main
```

- [ ] **Create `tools/deploy_devcluster_gcp.py`**

```python
#!/usr/bin/env python3
"""Deploy a GCP devcluster with Oxla and a client node.

Full lifecycle: terraform apply -> extract outputs -> ansible deploy -> wait for Oxla -> print info.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TERRAFORM_DIR = REPO_ROOT / "terraform" / "devcluster-gcp"
ANSIBLE_DIR = REPO_ROOT / "ansible"
AR_REGISTRY = "europe-west4-docker.pkg.dev"
AR_PROJECT = "testing-oxla"
AR_REPO = "oxla-daily"
DEFAULT_MACHINE_TYPE = "n2-standard-8"
SSH_KEY_DIR = Path.home() / ".ssh"


def get_latest_image_tag(gcp_project: str) -> str:
    """Query AR for the most recent oxla-daily image tag."""
    repo_path = f"{AR_REGISTRY}/{gcp_project}/{AR_REPO}"
    result = subprocess.run(
        [
            "gcloud", "artifacts", "docker", "images", "list", repo_path,
            "--project", gcp_project,
            "--include-tags",
            "--sort-by=~createTime",
            "--limit=1",
            "--format=value(tags)",
        ],
        capture_output=True,
        text=True,
    )
    tag = result.stdout.strip().split(";")[0] if result.returncode == 0 else ""
    if not tag:
        print("WARNING: Could not query AR for latest tag, falling back to 'latest'", file=sys.stderr)
        return f"{repo_path}:latest"
    image = f"{repo_path}:{tag}"
    print(f"  Resolved latest image: {image}")
    return image


def check_prerequisites():
    required = ["terraform", "ansible-playbook", "ansible-galaxy", "gcloud", "ssh"]
    missing = [cmd for cmd in required if shutil.which(cmd) is None]
    if missing:
        print(f"ERROR: Missing required tools: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)


def run(cmd, capture=False, env_extra=None, cwd=None):
    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)
    if capture:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, env=env)
        if result.returncode != 0:
            print(f"ERROR: Command failed: {' '.join(cmd)}", file=sys.stderr)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            sys.exit(1)
        return result
    result = subprocess.run(cmd, cwd=cwd, env=env)
    if result.returncode != 0:
        print(f"ERROR: Command failed (exit {result.returncode}): {' '.join(cmd)}", file=sys.stderr)
        sys.exit(1)
    return result


def terraform_output(name, required=True):
    result = subprocess.run(
        ["terraform", "output", "-raw", name],
        capture_output=True, text=True, cwd=TERRAFORM_DIR,
    )
    if result.returncode != 0:
        if required:
            print(f"ERROR: terraform output -raw {name} failed", file=sys.stderr)
            sys.exit(1)
        return None
    return result.stdout.strip() or None


def terraform_init():
    print("\n=== Terraform init ===")
    run(["terraform", "init"], cwd=TERRAFORM_DIR)


def terraform_apply(args):
    print("\n=== Terraform apply ===")
    cmd = ["terraform", "apply", "-auto-approve",
           f"-var=devcluster_alias={args.alias}",
           f"-var=devcluster_node_count={args.nodes}",
           f"-var=devcluster_machine_type={args.machine_type}",
           f"-var=gcp_project={args.gcp_project}"]
    run(cmd, cwd=TERRAFORM_DIR)


def terraform_destroy():
    print("\n=== Terraform destroy ===")
    run(["terraform", "destroy", "-auto-approve"], cwd=TERRAFORM_DIR)


def extract_outputs():
    print("\n=== Extracting terraform outputs ===")
    cluster_name = terraform_output("devcluster_name")
    password = terraform_output("oxla_password")
    client_ip = terraform_output("client_node_public_ip")

    inventory_path = ANSIBLE_DIR / "inventory" / f"{cluster_name}.yml"
    inventory_path.write_text(terraform_output("ansible_inventory"))
    print(f"  Inventory: {inventory_path}")

    SSH_KEY_DIR.mkdir(mode=0o700, exist_ok=True)
    ssh_key_path = SSH_KEY_DIR / f"{cluster_name}-key"
    key_content = terraform_output("ssh_private_key")
    if not key_content.endswith("\n"):
        key_content += "\n"
    ssh_key_path.write_text(key_content)
    ssh_key_path.chmod(0o600)
    print(f"  SSH key: {ssh_key_path}")

    return {"cluster_name": cluster_name, "ssh_key_path": ssh_key_path,
            "inventory_path": inventory_path, "password": password, "client_ip": client_ip}


def install_ansible_requirements():
    print("\n=== Installing ansible requirements ===")
    run(["ansible-galaxy", "collection", "install", "-r",
         str(ANSIBLE_DIR / "requirements.yml")], cwd=ANSIBLE_DIR)


def run_ansible_deploy(cluster_name, ssh_key_path, inventory_path, image, home_name, password):
    print("\n=== Running ansible deployment ===")
    extra_vars = f"image={image} oxla_home_name={home_name} disable_table_tasks=false oxla_password={password} devcluster_name={cluster_name.replace('-', '_')}"
    run(
        ["ansible-playbook", "devcluster_deploy_gcp.yml",
         "--inventory", str(inventory_path),
         "--private-key", str(ssh_key_path),
         "--extra-vars", extra_vars],
        cwd=ANSIBLE_DIR,
        env_extra={"ANSIBLE_HOST_KEY_CHECKING": "False"},
    )


def wait_for_oxla(ssh_key_path, host, password):
    print("\n=== Waiting for Oxla to be ready ===")
    psql_cmd = f'PGPASSWORD="{password}" psql -U oxla -h localhost -p 5432 -d oxla -c "SELECT 1"'
    for attempt in range(1, 121):
        result = subprocess.run(
            ["ssh", "-i", str(ssh_key_path), "-o", "StrictHostKeyChecking=no",
             "-o", "ConnectTimeout=5", f"ubuntu@{host}", psql_cmd],
            capture_output=True, text=True,
        )
        if result.returncode == 0:
            print("  Oxla is ready!")
            return
        print(f"  [{attempt}/120] not ready, waiting 5s...")
        time.sleep(5)
    print("ERROR: Oxla failed to start within 10 minutes", file=sys.stderr)
    sys.exit(1)


def print_connection_info(cluster_name, host, password, ssh_key_path, client_ip):
    print(f"""
{"=" * 72}
  DEVCLUSTER DEPLOYED SUCCESSFULLY
{"=" * 72}
  Cluster:  {cluster_name}
  Host:     {host}

  PostgreSQL:
    PGPASSWORD='{password}' psql -U oxla -h {host} -p 5432 -d oxla

  SSH (devcluster node):
    ssh -i {ssh_key_path} ubuntu@{host}

  SSH (client node):
    ssh -i {ssh_key_path} ubuntu@{client_ip}

  Destroy:
    python3 {__file__} destroy --gcp-project {AR_PROJECT}
{"=" * 72}
""")


def cmd_deploy(args):
    check_prerequisites()
    if args.image is None:
        args.image = get_latest_image_tag(args.gcp_project)
    if not args.skip_infra:
        terraform_init()
        terraform_apply(args)
    outputs = extract_outputs()
    if not args.skip_deploy:
        install_ansible_requirements()
        run_ansible_deploy(
            cluster_name=outputs["cluster_name"],
            ssh_key_path=outputs["ssh_key_path"],
            inventory_path=outputs["inventory_path"],
            image=args.image,
            home_name=args.home_name,
            password=outputs["password"],
        )
        node_public_ips = json.loads(subprocess.run(
            ["terraform", "output", "-json", "public_ips"],
            capture_output=True, text=True, cwd=TERRAFORM_DIR,
        ).stdout)
        wait_for_oxla(outputs["ssh_key_path"], node_public_ips[0], outputs["password"])
        print_connection_info(
            outputs["cluster_name"], node_public_ips[0],
            outputs["password"], outputs["ssh_key_path"], outputs["client_ip"],
        )


def cmd_status(args):
    check_prerequisites()
    terraform_init()
    cluster_name = terraform_output("devcluster_name")
    password = terraform_output("oxla_password")
    client_ip = terraform_output("client_node_public_ip")
    public_ips = json.loads(subprocess.run(
        ["terraform", "output", "-json", "public_ips"],
        capture_output=True, text=True, cwd=TERRAFORM_DIR,
    ).stdout)
    ssh_key_path = SSH_KEY_DIR / f"{cluster_name}-key"
    print_connection_info(cluster_name, public_ips[0], password, ssh_key_path, client_ip)


def cmd_destroy(args):
    check_prerequisites()
    terraform_init()
    try:
        cluster_name = terraform_output("devcluster_name")
    except SystemExit:
        cluster_name = None
    terraform_destroy()
    if cluster_name:
        for path in [SSH_KEY_DIR / f"{cluster_name}-key",
                     ANSIBLE_DIR / "inventory" / f"{cluster_name}.yml"]:
            if path.exists():
                path.unlink()
                print(f"  Removed: {path}")
    print("\n  Cluster destroyed.")


def main():
    parser = argparse.ArgumentParser(description="Deploy a GCP devcluster with Oxla")
    parser.add_argument("--gcp-project", default=AR_PROJECT, help=f"GCP project ID (default: {AR_PROJECT})")
    subparsers = parser.add_subparsers(dest="command", required=True)

    deploy = subparsers.add_parser("deploy", help="Create infra and deploy Oxla")
    deploy.add_argument("--alias", default="dev", help="Short cluster alias (default: dev)")
    deploy.add_argument("--nodes", type=int, default=1, help="Number of Oxla nodes (default: 1)")
    deploy.add_argument("--machine-type", default=DEFAULT_MACHINE_TYPE,
                        help=f"GCE machine type (default: {DEFAULT_MACHINE_TYPE})")
    deploy.add_argument("--image", default=None, help="Oxla Docker image (default: latest from AR)")
    deploy.add_argument("--home-name", default="home", help="Oxla home name (default: home)")
    deploy.add_argument("--skip-infra", action="store_true", help="Skip terraform, only run ansible")
    deploy.add_argument("--skip-deploy", action="store_true", help="Only create infra, skip ansible")
    deploy.set_defaults(func=cmd_deploy)

    status = subparsers.add_parser("status", help="Show cluster connection info")
    status.set_defaults(func=cmd_status)

    destroy = subparsers.add_parser("destroy", help="Tear down the cluster")
    destroy.set_defaults(func=cmd_destroy)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
```

- [ ] **Make executable and commit**
```bash
chmod +x /home/przemo/workspace/Oxla/tools/deploy_devcluster_gcp.py
cd /home/przemo/workspace/Oxla
git add tools/deploy_devcluster_gcp.py
git commit -m "tools: add deploy_devcluster_gcp.py for GCP devcluster lifecycle (DEVPROD-4314)"
```

---

## Manual Validation Gate (DEVPROD-4314)

**Before declaring phase 1 complete, run these three steps manually:**

- [ ] **Step 1: Provision a 1-node cluster**
```bash
cd /home/przemo/workspace/Oxla
python3 tools/deploy_devcluster_gcp.py --gcp-project testing-oxla deploy \
  --alias manual-test --nodes 1 --machine-type n2-standard-8
```
Expected: prints connection info, `psql` connects successfully.

- [ ] **Step 2: SSH into client node and run a blackbox test**
```bash
ssh -i ~/.ssh/gh-dev-n2-standard-8-1n-manual-test-key ubuntu@<CLIENT_IP>
git clone git@github.com:redpanda-data/Oxla.git
cd Oxla
OXLA_HOST=<FIRST_NODE_PRIVATE_IP> tox -e blackbox -- tests/blackbox/test_basic.py -k test_simple_select
```
Expected: test passes.

- [ ] **Step 3: Destroy and verify clean-up**
```bash
python3 tools/deploy_devcluster_gcp.py --gcp-project testing-oxla destroy
```
Then verify in GCP Console: no GCE instances and no GCS bucket named `oxla-gcp-1n-manual-test` remain.

---

## Self-Review Checklist

- [x] **Spec coverage:** All 6 PRs from design covered. Phase 2 (4315–4323) explicitly out of scope.
- [x] **No placeholders:** All code blocks are complete and runnable.
- [x] **Type consistency:** `devcluster_name` used consistently across TF outputs, Ansible extra-vars, and Python script. `cluster_name.replace('-', '_')` applied in the Python deploy script when passing to Ansible (matching existing AWS pattern).
- [x] **WIF provider resource name:** Task 18 notes that the project number for `devprod-cicd-infra` must be substituted — this is a known gap that requires one `gcloud` lookup at PR time.
