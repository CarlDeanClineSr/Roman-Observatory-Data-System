# Roman Data Vault

GitHub is the control plane, not the telescope-data warehouse.

When a separately reviewed download is eventually authorized, create a local or cloud root outside the repository and set:

```text
ROMAN_VAULT_ROOT=D:/ROMAN_DATA_VAULT
```

Suggested directories are listed in `config/vault.example.json`. Until product retrieval is approved, no vault is required.

Never commit FITS, ASDF, Parquet, archives, mosaics, or bulk catalogs to Git.
