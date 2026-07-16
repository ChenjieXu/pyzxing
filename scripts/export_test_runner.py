#!/usr/bin/env python3
"""Verify a downloaded Runner artifact and export its path for CI tests."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from verify_runner_artifact import read_checksum, sha256


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    parser.add_argument("--env-name", default="PYZXING_TEST_JAR")
    args = parser.parse_args()

    jars = sorted(args.directory.glob("*.jar"))
    if len(jars) != 1:
        raise ValueError(f"Expected exactly one Runner JAR in {args.directory}, found {jars}")

    jar = jars[0].resolve(strict=True)
    checksum_file = Path(f"{jar}.sha256")
    expected = read_checksum(checksum_file, jar.name)
    actual = sha256(jar)
    if actual != expected:
        raise ValueError(f"Runner checksum mismatch: expected {expected}, got {actual}")

    github_env = os.environ.get("GITHUB_ENV")
    if github_env:
        with Path(github_env).open("a", encoding="utf-8") as stream:
            stream.write(f"{args.env_name}={jar}\n")
    print(jar)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
