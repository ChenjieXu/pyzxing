#!/usr/bin/env python3
"""Install the canonical Runner and smoke fixture into a conda prefix."""

from __future__ import annotations

import argparse
import hashlib
import shutil
from pathlib import Path

from verify_version_sync import ROOT, read_python_constants



def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--jar", required=True, type=Path)
    parser.add_argument("--fixture", required=True, type=Path)
    parser.add_argument("--prefix", required=True, type=Path)
    args = parser.parse_args()

    config = read_python_constants(ROOT / "pyzxing" / "config.py", "Config")

    jar = args.jar.resolve(strict=True)
    fixture = args.fixture.resolve(strict=True)
    if jar.name != config["JAR_FILENAME"]:
        raise ValueError(
            f"canonical JAR is named {jar.name!r}, expected {config['JAR_FILENAME']!r}"
        )
    if config["JAR_SHA256"] == "0" * 64 or config["RUNNER_SOURCE_COMMIT"] == "":
        raise ValueError("conda builds require finalized Runner provenance in Config")
    actual_sha = sha256(jar)
    if actual_sha != config["JAR_SHA256"]:
        raise ValueError(
            f"canonical JAR SHA-256 is {actual_sha}, expected {config['JAR_SHA256']}"
        )

    share = args.prefix / "share" / "pyzxing"
    runner_dir = share / "runner"
    fixture_dir = share / "test-data"
    runner_dir.mkdir(parents=True, exist_ok=True)
    fixture_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(jar, runner_dir / jar.name)
    shutil.copy2(fixture, fixture_dir / fixture.name)
    print(runner_dir / jar.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
