# Roman Observatory Data System

Evidence-preserving public-information, archive-metadata, simulation, ground-test, and selected-data system for NASA's Nancy Grace Roman Space Telescope.

**Repository owner and project lead:** Carl Dean Cline Sr.

## Current state

```text
VERSION                         0.1.0
SOURCE REGISTRY                 FROZEN V1
DEFAULT RETRIEVAL MODE          METADATA ONLY
AUTOMATIC PRODUCT DOWNLOADS     DISABLED
SCHEDULED PROVIDER POLLING      DISABLED
ROMAN RESEARCH NEXUS SCRAPING   DISABLED
RITA / CaSSI PRODUCT ACCESS     RESTRICTED
NVCPP AUTOMATIC ACCESS          DISABLED
L1 SPACE-WEATHER ACCESS         FORBIDDEN
chi_B24M ACCESS                 FORBIDDEN
GANNON HOLDOUT ACCESS           FORBIDDEN
```

This repository is independent from LUFT and from NVCPP's Sun-Earth L1 space-weather system. Roman material may later publish a small, explicit, hashed export into NVCPP's **Astronomical Observatory** domain. Roman arrays, simulations, detector measurements, and derived telescope quantities must never enter L1 plasma calculations or be relabeled as `chi_B24M`.

## What v0.1.0 does

1. Freezes an approved Roman source registry built from NASA, STScI, MAST, IPAC, the Roman Research Nexus documentation, Roman CPP resources, `roman-corgi`, the Roman technical-information repository, and the official Roman Data Workshop.
2. Captures bounded public web responses and records retrieval time, HTTP status, selected headers, exact bytes, SHA-256, and change state.
3. Queries MAST through the documented `invoke` API for **metadata only**: the mission list and one explicitly named Roman collection count. Observation rows, product rows, and file retrieval are disabled.
4. Classifies records conservatively as `OFFICIAL_INFO`, `SIMULATED`, `GROUND_TEST`, an explicit `FLIGHT_*` class, or `UNKNOWN_QUARANTINE`.
5. Produces one small `nvcpp_approved_export.json` whose firewall fields remain closed to L1, plasma, `chi_B24M`, and the Gannon holdout.
6. Runs offline CI tests that prohibit cross-imports from NVCPP space-weather modules and prevent simulation or triplet-test records from being promoted to flight data.

## What v0.1.0 does not do

- It does not intercept or decode spacecraft communications.
- It does not scrape the authenticated Roman Research Nexus Hub.
- It does not claim access to restricted RITA, CaSSI telemetry, Level 0, or mission-operations files.
- It does not automatically download FITS, ASDF, Parquet, detector-test archives, or workshop example files.
- It does not install `romancal`, CRDS, or Roman pipeline environments into an NVCPP L1 environment.
- It does not make dark-energy, exoplanet, dark-matter, mission-performance, or life-detection claims.

## Do not run the workshop downloader yet

The official STScI workshop repository contains `data/download.py`, which downloads a fixed Build 22 collection of ASDF, Parquet, and JSON example products. That source list is preserved here in:

```text
config/workshop_build22_manifest.v1.json
```

The manifest is classified as **official STScI simulated/training data**, not flight data, and contains:

```text
automatic_download = false
execution_authorized = false
```

Do **not** copy the external downloader into a Colab cell or run it against Google Drive during the bootstrap stage. The first successful Roman-data action is a hashed catalog of what exists, not a large file on disk.

## Repository versus data vault

Git stores code, contracts, tests, source manifests, and small reports. Large products belong outside Git in a separate vault named by `ROMAN_VAULT_ROOT`.

```text
Roman-Observatory-Data-System/   code and small evidence
ROMAN_DATA_VAULT/                FITS, ASDF, Parquet, archives, mosaics, catalogs
```

A suggested Windows layout is documented in `config/vault.example.json` and `docs/VAULT_LAYOUT.md`. Creating the vault is optional for v0.1 because no product download is enabled.

## Data-level naming rule

A bare label such as `L1` is forbidden in shared records because it can mean two unrelated things:

```text
SUN_EARTH_L1_SPACE_WEATHER    location/domain near the Sun-Earth L1 point
WFI_LEVEL_1                   Roman WFI product processing level
CGI_LEVEL_1                   Roman Coronagraph product processing level
CGI_LEVEL_2A / CGI_LEVEL_2B   Roman Coronagraph pipeline levels
```

Always use the namespaced form.

## Local quick start

Python 3.12 or later:

```bash
python -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1

python -m pip install -e ".[dev]"
roman-watch validate
pytest
```

Provider-facing commands remain manual:

```bash
# Bounded public page evidence only
roman-watch source-watch --outdir runs/roman/source_watch

# Mission list + Roman collection counts only; no observation/product rows
roman-watch mast-catalog --outdir runs/roman/mast_catalog

# Build a small firewall-safe export from a completed manifest
roman-watch export \
  --source-manifest runs/roman/mast_catalog/mast_catalog_manifest.json \
  --out nvcpp_approved_export.json
```

## Important contracts

| File | Purpose |
|---|---|
| `config/sources.v1.json` | Frozen Roman source registry |
| `config/download_policy.v1.json` | Metadata-first retrieval and size limits |
| `config/product_classes.v1.json` | Origin classes and namespaced data levels |
| `config/mast_metadata.v1.json` | Mission-list and collection-count-only MAST contract |
| `config/workshop_build22_manifest.v1.json` | Frozen official workshop file list, downloads disabled |
| `config/nvcpp_export_contract.v1.json` | Narrow Roman-to-NVCPP astronomical export boundary |
| `config/bootstrap_freeze.v1.json` | SHA-256 freeze of every v0.1 control contract |

## GitHub workflows

Deterministic review workflows:

```text
Roman System CI / audit
Roman Provenance Guard / guard
```

Provider-dependent workflows are manual and should not become required merge checks:

```text
Roman Public Source Watch
Roman MAST Metadata Watch
```

A NASA, STScI, MAST, IPAC, GitHub, or documentation outage should create an evidence-bearing operational failure, not block unrelated code review.

## Next controlled sequence

```text
initial commit and offline CI
    -> inspect both required checks
    -> run one manual source watch
    -> inspect source hashes and change states
    -> run one manual MAST metadata watch
    -> inspect the mission list, collection counts, hard caps, and zero-row/zero-download assertions
    -> stop for another review before any observation or product metadata is enabled
    -> only then consider one separately approved small data product
```

No software license has been selected yet. Repository reuse terms should be chosen deliberately by the owner in a later change.
