# Contributing

Add or update an extension by opening a pull request that changes `index.json` only (see "Submitting an extension" in the
README). Never edit `index.json.sig` and never commit a private key.

Before you open the pull request:

```
python3 scripts/check_index.py index.json
```

It checks the format rules and downloads each package to verify its hash and size. Maintainers sign the index after merging.

Published versions are immutable: to change an extension, release a new version. Keep the package URL serving the same bytes
forever.
