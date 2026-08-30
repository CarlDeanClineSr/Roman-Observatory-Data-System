# Operator Next Steps

## Now

1. Let the two offline GitHub Actions checks finish.
2. Do not run the STScI workshop downloader.
3. Do not create a Colab download cell.
4. Do not clone WFI triplet-test archives.
5. Do not add Roman dependencies to an NVCPP L1 environment.

## After offline checks are green

Run **Roman Public Source Watch** once from the Actions tab. Review the uploaded manifest and confirm:

```text
products_downloaded = 0
automatic_product_downloads_enabled = false
all source IDs match config/sources.v1.json
raw hashes exist for successful captures
Nexus authenticated Hub remained disabled
JPL HTTP 403 is RESTRICTED / CDN_RESTRICTED
failed_source_count counts only unavailable captures, not the expected JPL boundary
```

After the source-watch review, the only allowed MAST increment is the narrowed **Roman MAST Metadata Watch**. Before dispatch, confirm its contract states:

```text
query_scope = MISSION_LIST_AND_COLLECTION_COUNTS_ONLY
observation_rows_enabled = false
product_rows_enabled = false
products_downloaded = 0
flight_data_assumed = false
```

When that artifact is eventually reviewed, stop again. Observation rows, product lists, file downloads, and an NVCPP export remain separately review-gated.
