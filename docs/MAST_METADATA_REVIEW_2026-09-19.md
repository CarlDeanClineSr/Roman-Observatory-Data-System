# First MAST metadata watch: reviewed September 19, 2026

Outcome: **accepted as a successful count-only archive check**. No observation
rows, product lists, product downloads, or NVCPP export are authorized by this
review.

## Evidence identity

- [Workflow run 35447598988](https://github.com/CarlDeanClineSr/Roman-Observatory-Data-System/actions/runs/35447598988)
- Commit: `f04f26fe2bd7d5e783029307632df9162e523964`
- Artifact: `roman-mast-metadata-35447598988` (ID `10586605683`)
- Downloaded ZIP SHA-256, verified against the published digest:
  `640677d0b02fba4d62d3f84dc70b82271e7d869a1c085a3d57c6d36259c4b88a`
- Manifest timestamp: `2026-09-19T14:04:13.429976+00:00`

## Manifest and raw-response checks

| Field | Recorded value |
|---|---:|
| Status | `SUCCESS` |
| Mission-list rows | 24 |
| Roman collection count | 11,226 |
| Collection queries / cap | 1 / 1 |
| Count-response rows / cap | 1 / 1 |
| Observation queries / rows | 0 / 0 |
| Product queries / rows | 0 / 0 |
| Products downloaded | 0 |
| `metadata_only` | `true` |
| `flight_data_assumed` | `false` |
| Errors | none |

Both raw MAST responses returned HTTP 200 and MAST `COMPLETE`. Their recorded
SHA-256 values are:

- Mission list: `1d4f38b07f1ceeae5ca2cc0855ef83138feb57839d12821e9f0dcf7ccfd65ae8`
- Collection count: `56d46db1ffee6ca3adc2b3c9cb9a910c178573ed13c1241943834106316a0ace`

The archive listed `ROMAN`; the count query requested `Roman`. The 11,226 value
counts collection records at this time. It is not a count of confirmed flight
images, unique exposures, downloaded files, or scientifically usable products.
No flight/ground/simulation origin was established by these two queries.

All four firewall flags remained false: Sun-Earth L1 space weather, plasma
pipeline, `chi_B24M`, and Gannon holdout access.

## Maintenance prompted by the run

The run succeeded but warned about Node 20 actions and an upcoming
`ubuntu-latest` migration. Repository-managed workflows now select Node 24
action majors (`checkout@v6`, `setup-python@v6`, `upload-artifact@v7`) and
`ubuntu-24.04`. This does not change query limits, Python 3.12, manual triggers,
artifact retention, or the seven frozen bootstrap contracts.

The original run and its annotations remain historical evidence. Maintenance
changes apply only to subsequent runs from the updated revision.
