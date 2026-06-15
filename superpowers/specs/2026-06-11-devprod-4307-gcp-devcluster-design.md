# DEVPROD-4307: Oxla devcluster blackbox tests on GCP — Design

**Epic:** https://redpandadata.atlassian.net/browse/DEVPROD-4307  
**Phase covered:** Stories 4308–4314 (infrastructure + manual validation gate)  
**Repos:** `devprod-infra`, `Oxla`

---

## Goal

Run all Oxla devcluster blackbox tests on GCP with full parity to AWS. This design covers
the first phase: standing up the infrastructure and tooling up to the manual validation
gate (DEVPROD-4314). The test job stories (4315–4323) are planned after the gate passes.

---

## Prerequisites (manual, block all PRs)

These must be completed by Ivo before any PR can be applied:

**0a — GCP project creation (Ivo):** ✅ DONE
- Project `testing-oxla` created in `redpanda.com` org
- Project ID: `testing-oxla`, Project number: `265247854512`
- Billing linked: `billingAccounts/0197D7-A02C67-8BD1C4` ✅
- Still needed: APIs enabled, and grant
  `tf-devprod-infra@devprod-cicd-infra.iam.gserviceaccount.com` `roles/owner` on
  `testing-oxla` (bootstrap — same pattern as `production-devprod` and `testing-devprod`)

**0b — TFC workspace creation:**
- New workspace `testing-oxla` in TFC org `redpanda-data`
- Points at `devprod-infra/testing-oxla/`
- Dynamic credentials via `tf-devprod-infra` TFC SA (same as existing devprod workspaces)
- Workspace variables: `project_id = testing-oxla`, `region = europe-west4`

---

## Architecture

```
devprod-infra/
├── gcp-oidc/          # existing — add Oxla WIF providers + SAs (PR 1, DEVPROD-4309)
└── testing-oxla/      # new — project resources (PR 2, DEVPROD-4308)

Oxla/
├── terraform/devcluster-gcp/   # new TF module (PR 3, DEVPROD-4310)
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── userdata.sh             # GCP bootstrap (PR 4, DEVPROD-4311)
│   └── templates/
│       └── ansible-inventory.yml.tpl   # includes client node
├── ansible/
│   └── devcluster_deploy_gcp.yml       # GCP Ansible playbook (PR 4, DEVPROD-4312)
├── .github/workflows/
│   └── create_multiarch_image.yml      # add AR push (PR 5, DEVPROD-4313)
└── tools/
    └── deploy_devcluster_gcp.py        # manual validation tool (PR 6, DEVPROD-4314)
```

---

## PR sequence

> PRs are merged in order; each depends on the previous being applied in TFC/GHA.

### PR 1 — DEVPROD-4309: WIF + service accounts (`devprod-infra/gcp-oidc/`)

**Convention:** follows existing pattern — `gcp-oidc/` owns all WIF pools and SA creation;
resource workspaces reference the known SA emails for IAM grants.

Changes to `gcp-oidc/main.tf`:
- Add provider alias `google.testing_oxla` pointing at project `testing-oxla`
- Grant `tf-devprod-infra` SA the roles needed to manage `testing-oxla`:
  - `roles/iam.serviceAccountAdmin` (create per-cluster SAs)
  - `roles/compute.admin` (manage GCE)
  - `roles/storage.admin` (manage GCS)
  - `roles/artifactregistry.admin` (manage AR repos + IAM)
  - `roles/iam.workloadIdentityPoolAdmin` on `devprod-cicd-infra` (to add provider to existing pool)
- Add WIF OIDC provider for `Oxla` repo in the existing `devprod-cicd-infra` pool
  (reuses `modules/gh-id-provider` pattern)
- Create `oxla-ci-github@testing-oxla` SA (infra SA) in `testing-oxla` via provider alias
- Create `oxla-ci-build@testing-oxla` SA (build SA) in `testing-oxla` via provider alias
- WIF bindings: bind pool subjects to these SAs
- IAM grants on `testing-oxla`:
  - `oxla-ci-github`: `roles/compute.admin` (scoped by label `managed-by=oxla-ci`
    via condition), `roles/storage.admin`, `roles/iam.serviceAccountAdmin`,
    `roles/artifactregistry.reader`
  - `oxla-ci-build`: `roles/artifactregistry.writer`

### PR 2 — DEVPROD-4308: Project resources (`devprod-infra/testing-oxla/`)

New TFC workspace. Assumes project exists (created by Ivo in step 0a).
SA emails are known at write time so no TF cross-workspace dependency.

`main.tf`:
- Enable required APIs (Compute Engine, Cloud Storage, IAM, Resource Manager, AR)
- VPC `testing-oxla-vpc` + subnet `testing-oxla-subnet` in `europe-west4` (10.0.0.0/16)
- Firewall rules: SSH (22), Oxla (5432), Node Exporter (9100), internal VPC (all)
- GCS bucket `testing-oxla-terraform-state` (Terraform backend for devcluster-gcp)
- GCS bucket `oxla-devcluster-home-blueprint-testing-oxla` (versioning enabled)
- GCS buckets for shared test data (determined after Phase 1 investigation in 4308)
- AR Docker repos: `oxla-daily`, `oxla-compilation` (confirm full list from ECR)
- IAM grants on AR repos:
  - `oxla-ci-github@testing-oxla` → `roles/artifactregistry.reader`
  - `oxla-ci-build@testing-oxla` → `roles/artifactregistry.writer`
  - Per-cluster SA (template) → `roles/artifactregistry.reader`

`variables.tf`: `project_id`, `region = europe-west4`
`outputs.tf`: VPC name, subnet name, bucket names, AR repo URLs

### PR 3 — DEVPROD-4310: Terraform module (`Oxla/terraform/devcluster-gcp/`)

New module parallel to `terraform/devcluster/`. Provisions N GCE devcluster nodes +
1 GCE client node in `testing-oxla-vpc`, `europe-west4`.

Key design points:
- Architecture auto-detected from machine type prefix: `t2a-*` → ARM, else x86
- Ubuntu 22.04, 256 GB `pd-ssd` boot disk
- ED25519 SSH key generated via `tls_private_key`, stored in per-cluster GCS bucket
- Per-cluster SA created by Terraform (attached to all GCE instances for AR pull + GCS access)
- Client node: GitHub deploy key or token injected via GCE metadata (enables `git clone`)
- Firewall rules: SSH (22), Oxla (5432), Node Exporter (9100), internal VPC
- GCS backend pointing at `testing-oxla-terraform-state`
- `outputs.tf` shape identical to `terraform/devcluster/outputs.tf`:
  `ansible_inventory`, `devcluster_name`, `ssh_private_key`, `oxla_password`,
  `client_node_public_ip` (new: exposes client node IP)
- Ansible inventory template includes `[client]` group alongside `[oxla_nodes]`

Naming convention: `gh-dev-<machine-type-sanitised>-<Nn>-<alias>` (same as AWS)

### PR 4 — DEVPROD-4311 + 4312: userdata + Ansible (one PR, parallelisable work)

**`terraform/devcluster-gcp/userdata.sh`** (DEVPROD-4311):

Based on `terraform/devcluster/userdata.sh`. AWS-specific sections replaced:

| AWS | GCP |
|-----|-----|
| AWS CLI + IMDSv2 credential fetch | google-cloud-sdk (SA auto-auth) |
| `docker-credential-ecr-login` | `gcloud auth configure-docker` |
| ECR registry in `~/.docker/config.json` | `europe-west4-docker.pkg.dev` registry |

Preserved unchanged: Docker install, Node Exporter (port 9100), kernel coredump path,
cloud-init completion signal, blueprint copy (`gsutil` / `gcloud storage` instead of `aws s3`).

Client node bootstrap (additional): Python 3, pip, git, tox (needed to run blackbox tests).

**`ansible/devcluster_deploy_gcp.yml`** (DEVPROD-4312):

Based on `ansible/devcluster_deploy_aws.yml`. Cloud-specific replacements:

| AWS playbook | GCP playbook |
|---|---|
| IMDSv2 credential fetch play | removed (SA auto-auth) |
| `aws s3 rm` (clean home) | `gcloud storage rm` |
| `aws ecr get-login-password` | `gcloud auth print-access-token` |
| `oxla_home_path: s3://...` | `oxla_home_path: gs://...` |
| `[oxla_nodes]` inventory only | `[oxla_nodes]` + `[client]` inventory groups |

All Oxla orchestration plays (deploy container, wait for cluster, port config, stop/clean)
preserved unchanged.

### PR 5 — DEVPROD-4313: Build pipeline → push to GCP AR

Identify which workflow currently pushes to ECR (likely `create_multiarch_image.yml`).
Add a parallel push to `testing-oxla` AR repositories.

Changes:
- Add `permissions: id-token: write` if not already present
- Add step: authenticate to GCP via WIF using `oxla-ci-build@testing-oxla` SA
- Add step: `gcloud auth configure-docker europe-west4-docker.pkg.dev`
- Add step: `docker push europe-west4-docker.pkg.dev/testing-oxla/<repo>:<tag>` for each image
- ECR push path: unchanged

Acceptance gate: GCE instance in `testing-oxla` can `docker pull` the pushed image.

### PR 6 — DEVPROD-4314: `tools/deploy_devcluster_gcp.py` + manual validation gate

GCP equivalent of `tools/deploy_devcluster.py`. Same subcommands: `deploy`, `status`,
`logs`, `destroy`.

| AWS (`deploy_devcluster.py`) | GCP (`deploy_devcluster_gcp.py`) |
|---|---|
| `terraform/devcluster` | `terraform/devcluster-gcp` |
| `aws ecr describe-images` | `gcloud artifacts docker images list` |
| `--aws-profile` | `--gcp-project` |
| `devcluster_deploy_aws.yml` | `devcluster_deploy_gcp.yml` |
| `ECR_REGISTRY` | `AR_REGISTRY = europe-west4-docker.pkg.dev/testing-oxla` |

Prerequisites check: `terraform`, `ansible-playbook`, `gcloud`, `ssh`.

**Manual validation gate** (must pass before 4315 work starts):
1. Provision 1-node cluster: `psql` connects successfully on port 5432
2. SSH into GCE client node, `git clone` repo, run one blackbox test manually
3. Destroy cluster, confirm all GCE instances + GCS bucket cleaned up

---

## Key decisions

| Decision | Choice | Reason |
|---|---|---|
| WIF pool location | Reuse existing pool in `devprod-cicd-infra` | Follows current convention; `gcp-oidc/` is the single source of truth for WIF |
| SA location | `testing-oxla` (not `devprod-cicd-infra`) | Project-scoped SAs match the `testing-oxla` isolation goal |
| TF workspace | Separate `testing-oxla` workspace | Mirrors `gcp-artifact-registry` pattern; clean separation |
| Module structure | Copy + adapt (not shared module) | AWS/GCP differ too much; shared abstraction would add complexity without benefit |
| PR 4 (4311+4312) | One PR for both | Userdata and Ansible are parallel work on the same PR branch; tested together |

---

## What is NOT in this design

Stories 4315–4323 (GHA workflows, test job adjustments, daily_checks) are out of scope
for this design. They are planned after the manual validation gate (DEVPROD-4314) passes.
