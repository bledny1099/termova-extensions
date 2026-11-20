# Termova extension catalog

The catalog that the Store in Termova (Mac, iPhone and iPad) reads by default. It is two static files:

```
index.json        the catalog
index.json.sig    base64 of the Ed25519 signature of the exact bytes of index.json
```

Termova fetches both from

```
https://raw.githubusercontent.com/bledny1099/termova-extensions/main/index.json
```

and checks the signature against the store key built into the app before it reads a single field. Packages live wherever their
authors host them (a release asset of this repository works); the index only points at them and pins their SHA-256 and signing
key. Nothing here runs code.

## Store public key

```
3TBLYvNE2VZgVb1nclsh2/5nsvfxr1qHdpptc61M68k=
```

Ed25519, base64 of the 32 raw bytes (fingerprint `a4b8e26710a7a64887c2a3271d8317b2`). Only the maintainers hold the private key and
sign `index.json.sig` after merging a pull request. Check what you cloned with `termova-ext index verify --store-key <key>`.

The three sample extensions are signed by the Termova author key `Ls4+YDWCkKu2l0zUqKH9QzAAiqjqiAxVIMUeo0/Hy3g=`.

## Format

```json
{
  "formatVersion": 1,
  "generatedAt": "2026-11-20T00:00:00Z",
  "extensions": [{
    "id": "com.example.deploy-helper",
    "name": "Deploy helper",
    "description": "Notifies when a deploy finishes.",
    "author": "Example Author",
    "authorPublicKey": "<base64, 32 bytes>",
    "categories": ["workflow"],
    "homepage": "https://example.com/deploy-helper",
    "versions": [{
      "version": "1.2.0",
      "minTermova": "0.16.0",
      "packageURL": "https://example.com/deploy-helper-1.2.0.termovaext",
      "sha256": "<64 lowercase hex of the whole .termovaext file>",
      "size": 18342,
      "permissions": ["terminal.read", "notifications"],
      "publishedAt": "2026-11-17T10:00:00Z"
    }]
  }]
}
```

The client rejects the whole index if a rule is broken: `formatVersion` is `1`; ids are unique; `authorPublicKey` is a 32-byte
key in base64; every `sha256` is 64 lowercase hex characters; every `packageURL` is https; `version` and `minTermova` are semver.
A listed package must hash to `sha256`, be signed by exactly `authorPublicKey`, and its manifest must agree with the entry
(`id`, `version`, `minTermova` and the same set of `permissions`). `scripts/check_index.py` checks these rules and downloads each
package to verify its hash and size.

## Submitting an extension

1. Make an author key once: `termova-ext keygen`. Keep the private key off every repository. The public key identifies you: every
   later version of the same id must be signed with it.
2. Build and sign: `termova-ext build`, `termova-ext validate --strict`, `termova-ext pack --key <your key>`.
3. Host the package at a stable https URL that keeps serving exactly that file (a GitHub release asset works).
4. Open a pull request that adds your version:

   ```
   termova-ext index add my-ext-1.0.0.termovaext --url https://example.com/my-ext-1.0.0.termovaext \
       --categories workflow --homepage https://example.com/my-ext
   ```

   `index add` refuses an unsigned package, a different author key for an id that is already listed, and a version that already
   exists with different bytes (published versions are immutable: bump the version). Do not touch `index.json.sig`.
5. A maintainer reviews the manifest and the code behind the hash, with the permissions in front of them (`termova-ext inspect`).

The extension format and CLI are documented in the Termova repository docs (`docs/EXTENSIONS.md`).

## Review rules

A pull request is declined for: permissions out of proportion to the purpose; `terminal.read` together with a `network:` host the
extension has no reason to talk to; obfuscated or minified-only code with no source; a name or icon that imitates another product;
an unreachable package URL or one that does not serve the pinned bytes. A signature proves who published a package, not that the
author is trustworthy: review is the control for that. A new version that adds permissions makes Termova ask the user again.

Changing the author key of an existing id is not something the tool does. It is a manual, reviewed change.

## License

The contents of this repository (the index, scripts and documentation) are MIT licensed, see `LICENSE`. Every listed extension is
licensed by its own author under the terms in its package.
