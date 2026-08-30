# Frozen Source Registry

`config/sources.v1.json` is the source authority for v0.1. Additions or changes require code review and a version change.

The registry separates:

- mission and technical information;
- MAST archive metadata;
- public ground-test releases;
- simulation indexes and software;
- authenticated or restricted resources;
- pinned external source files such as the STScI workshop manifest.

A configured URL is fetched only when all of these are true:

```text
enabled = true
capture_raw_response = true
access is safe for unauthenticated public capture
host is present in the download policy allowlist
```

The watcher fetches only the configured URL. It does not crawl links or download products referenced by the page.
