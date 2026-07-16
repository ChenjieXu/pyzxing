#!/usr/bin/env python3
"""Verify canonical Runner assets against the committed pyzxing configuration."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from urllib.parse import unquote, urlparse

from verify_runner_artifact import read_checksum, sha256
from verify_version_sync import ROOT, read_python_constants


COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--jar", required=True, type=Path)
    parser.add_argument("--checksum", required=True, type=Path)
    parser.add_argument("--source-commit", required=True, type=Path)
    parser.add_argument("--reproducibility", required=True, type=Path)
    parser.add_argument("--release-tag", required=True)
    args = parser.parse_args()

    config = read_python_constants(ROOT / "pyzxing" / "config.py", "Config")

    jar = args.jar.resolve(strict=True)
    expected = read_checksum(args.checksum.resolve(strict=True), jar.name)
    actual = sha256(jar)
    if actual != expected:
        raise ValueError(f"Canonical Runner checksum mismatch: expected {expected}, got {actual}")

    configured_sha = config["JAR_SHA256"].lower()
    if configured_sha != actual:
        raise ValueError(
            f"Config.JAR_SHA256 is {configured_sha}, but the canonical Runner is {actual}"
        )

    configured_url = (
        config["JAR_URL_PREFIX"].format(version=config["JAR_RELEASE_VERSION"])
        + config["JAR_FILENAME"]
    )
    configured_name = Path(unquote(urlparse(configured_url).path)).name
    if configured_name != jar.name:
        raise ValueError(
            f"Config.get_jar_url() names {configured_name!r}, expected {jar.name!r}"
        )
    if f"/download/{args.release_tag}/" not in urlparse(configured_url).path:
        raise ValueError(
            f"Config.get_jar_url() does not point at release {args.release_tag}: {configured_url}"
        )

    source_commit = args.source_commit.read_text(encoding="ascii").strip()
    if COMMIT_RE.fullmatch(source_commit) is None:
        raise ValueError("runner-source-commit.txt must contain one lowercase full commit SHA")

    configured_source = config["RUNNER_SOURCE_COMMIT"]
    if configured_source != source_commit:
        raise ValueError(
            "The committed Runner source commit does not match runner-source-commit.txt: "
            f"{configured_source!r} != {source_commit!r}"
        )

    reproducibility = args.reproducibility.resolve(strict=True).read_text(
        encoding="ascii"
    ).splitlines()
    expected_reproducibility = [
        "reproducible=true",
        f"source_commit={source_commit}",
    ]
    if reproducibility != expected_reproducibility:
        raise ValueError(
            "runner-reproducibility.txt must prove two byte-identical clean builds "
            f"for {source_commit}; got {reproducibility!r}"
        )

    print(source_commit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
