# Companion NVCPP Roman Status — November 23, 2026

## Mission context

NASA's October 22 report said Roman had entered its science commissioning phase. NASA's November 13 update reports that the observatory's optics and instruments have been brought into precise alignment. NASA describes this as another step toward science operations and says the team will next exercise more than 3,000 moving parts in the Coronagraph deformable mirrors. This is a commissioning milestone, not confirmation that routine survey science operations have begun.

On November 23, NASA announced that Roman's first images will be revealed at AGU26 on December 7, 2026. As of this review, the release is scheduled for a future date; those images have not yet been reviewed here. NASA's November 20 WFI Cycle 2 call for proposals opened November 18 and lists a February 24, 2027 due date. Proposal activity is not a substitute for instrument commissioning or archive-product validation.

Official references:
- NASA, November 13 instrument alignment update: https://science.nasa.gov/blogs/roman/2026/11/13/instruments-on-nasas-roman-space-telescope-get-in-sync-for-science/
- NASA, November 23 first-image announcement: https://science.nasa.gov/astrophysics/programs/physics-of-the-cosmos/community/romans-first-images-to-be-revealed/
- NASA, November 20 Cycle 2 WFI call: https://science.nasa.gov/astrophysics/programs/cosmic-origins/community/roman-space-telescope-cycle-2-call-for-proposals/

## Separate NVCPP readiness observation

The sibling NVCPP repository recorded Roman MAST results in workflow run [45240545852](https://github.com/CarlDeanClineSr/NVCPP-Non-Voxelated-Computational-Physics-Portal-/actions/runs/45240545852), dated November 23, 2026:

| MAST collection query | CAOM rows |
|---|---:|
| `Roman` | 476,611 |
| `ROMAN` | 476,636 |

The two case variants returned different counts and response hashes. They are separate query results and must not be summed as independent holdings or described as unique exposures. Both bounded 25-row metadata-sample requests timed out. The NVCPP workflow completed successfully at the Actions level, but its internal readiness report was `PARTIAL`.

Inspection of the run artifact found a filename collision: case-folded output names caused the `Roman` and `ROMAN` raw count responses to target the same path, leaving only one response body in the ZIP. The sibling NVCPP review branch is correcting this and adding a regression test. The run did not download or inspect ASDF/FITS product bytes.

These are sibling-project observations only. They do not change this repository's MAST contract, authorize observation-row or product-row queries here, or enable data transfer to NVCPP.

## This repository's operating boundary remains unchanged

`Roman-Observatory-Data-System` remains at v0.1.0 with its frozen source registry and metadata-only retrieval policy:

- Mission list and explicitly configured collection counts only.
- Observation rows, product rows, and file retrieval remain disabled.
- Automatic product downloads and scheduled provider polling remain disabled.
- Roman Research Nexus scraping remains disabled; RITA/CaSSI access remains restricted.
- NVCPP automatic access remains disabled.
- Roman data remain outside Sun-Earth L1 space-weather calculations, `chi_B24M`, and the Gannon holdout.
- The STScI workshop downloader remains disabled; workshop Build 22 examples remain classified as simulated/training material.

This status note is contextual documentation. It does not modify the frozen v1 contracts, grant new data access, or authorize a product download.

## Next review point

After the scheduled December 7 first-image announcement, review the actual NASA release and any associated official archive documentation. Treat the image release, public catalog metadata, product-level availability, and commissioning status as separate evidence. Any observation-row query, product download, or NVCPP export still requires its own explicit review and approval.

