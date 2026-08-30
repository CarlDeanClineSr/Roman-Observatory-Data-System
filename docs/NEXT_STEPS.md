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
```

Then run **Roman MAST Metadata Watch** once and confirm:

```text
metadata_only = true
products_downloaded = 0
flight_data_assumed = false
ambiguous rows remain UNKNOWN_QUARANTINE
```

Only after those reviews should the first small NVCPP astronomical export be created.
