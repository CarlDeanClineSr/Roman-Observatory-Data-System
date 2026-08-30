# STScI Roman Data Workshop Example List

The code supplied by the operator is the official `data/download.py` file from the public `spacetelescope/roman-data-workshop` repository at the pinned source recorded in `config/workshop_build22_manifest.v1.json`.

It performs real downloads. It does not merely inspect metadata. It iterates through 36 fixed example paths under the STScI science-data redirector and moves the retrieved ASDF, Parquet, and JSON files next to the script.

For that reason, v0.1 does **not** include or execute the downloader. The exact remote paths are retained as data, with:

```text
origin_class         SIMULATED
automatic_download   false
execution_authorized false
flight_data          false
```

Later, one small item can be authorized through a new contract after its remote size, hash support, storage destination, documentation, and purpose are reviewed.
