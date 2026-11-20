#!/usr/bin/env python3
"""Checks index.json against the Termova store format rules (stdlib only).

Usage: check_index.py [index.json] [--offline]

Rules: formatVersion 1, unique ids, base64 32-byte author keys, lowercase sha256, https URLs, semver.
Unless --offline is given, every packageURL is downloaded and its sha256 and size are verified.
The Ed25519 signature of index.json is checked by the maintainers with `termova-ext index verify`.
"""
import base64
import binascii
import hashlib
import json
import re
import sys
import urllib.request

SEMVER = re.compile(r"^\d+\.\d+\.\d+(-[0-9A-Za-z.-]+)?(\+[0-9A-Za-z.-]+)?$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
MAX_PACKAGE = 20 * 1024 * 1024
errors = []


def err(msg):
    errors.append(msg)


def check_key(where, value):
    try:
        raw = base64.b64decode(value, validate=True)
    except (binascii.Error, TypeError, ValueError):
        return err(f"{where}: authorPublicKey is not base64")
    if len(raw) != 32:
        err(f"{where}: authorPublicKey must be 32 bytes, got {len(raw)}")


def download(url):
    req = urllib.request.Request(url, headers={"User-Agent": "termova-extensions-check"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read(MAX_PACKAGE + 1)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    offline = "--offline" in sys.argv
    path = args[0] if args else "index.json"
    with open(path, "rb") as f:
        try:
            index = json.loads(f.read().decode("utf-8"))
        except ValueError as e:
            print(f"{path}: not valid JSON: {e}")
            return 1
    if index.get("formatVersion") != 1:
        err("formatVersion must be 1")
    exts = index.get("extensions")
    if not isinstance(exts, list):
        err("extensions must be a list")
        exts = []
    seen = set()
    for e in exts:
        eid = e.get("id", "")
        where = eid or "<no id>"
        if not eid:
            err("an entry has no id")
        if eid in seen:
            err(f"{where}: duplicate id")
        seen.add(eid)
        for field in ("name", "description", "author"):
            if not e.get(field):
                err(f"{where}: missing {field}")
        check_key(where, e.get("authorPublicKey", ""))
        for field in ("icon", "homepage"):
            if e.get(field) and not e[field].startswith("https://"):
                err(f"{where}: {field} must be https")
        versions = e.get("versions") or []
        if not versions:
            err(f"{where}: no versions")
        vseen = set()
        for v in versions:
            vw = f"{where} {v.get('version')}"
            if not SEMVER.match(str(v.get("version", ""))):
                err(f"{vw}: version is not semver")
            if not SEMVER.match(str(v.get("minTermova", ""))):
                err(f"{vw}: minTermova is not semver")
            if v.get("version") in vseen:
                err(f"{vw}: duplicate version")
            vseen.add(v.get("version"))
            url = str(v.get("packageURL", ""))
            sha = str(v.get("sha256", ""))
            size = v.get("size")
            if not url.startswith("https://"):
                err(f"{vw}: packageURL must be https")
            if not HEX64.match(sha):
                err(f"{vw}: sha256 must be 64 lowercase hex characters")
            if not isinstance(size, int) or size <= 0 or size > MAX_PACKAGE:
                err(f"{vw}: size must be a positive integer up to {MAX_PACKAGE}")
            if offline or not url.startswith("https://") or not HEX64.match(sha):
                continue
            try:
                data = download(url)
            except Exception as ex:  # a network failure fails this entry
                err(f"{vw}: cannot download {url}: {ex}")
                continue
            if hashlib.sha256(data).hexdigest() != sha:
                err(f"{vw}: sha256 of {url} does not match the index")
            if isinstance(size, int) and len(data) != size:
                err(f"{vw}: size is {len(data)}, index says {size}")
    if errors:
        for m in errors:
            print("error:", m)
        return 1
    print(f"ok: {len(exts)} extension(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
