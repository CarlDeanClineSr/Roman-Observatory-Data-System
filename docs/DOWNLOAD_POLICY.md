# Download Policy

The v0.1 default is `METADATA_ONLY`.

```text
automatic_product_downloads_enabled = false
external_download_scripts_execute_automatically = false
```

The 250 MB individual ceiling and 1 GB daily budget are dormant engineering limits for a later reviewed downloader. They do not authorize any current retrieval.

Large ASDF, FITS, Parquet, HDF5, Zarr, and archive containers are blocked from automatic retrieval. Restricted products remain metadata-only. Partial files must never be accepted as completed evidence.

There is deliberately no product-download CLI command in v0.1.
