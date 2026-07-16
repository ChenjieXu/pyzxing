#!/usr/bin/env python3
"""Create or verify the checksum file for a pyzxing Runner JAR."""

from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path


CHECKSUM_RE = re.compile(r"^([0-9a-fA-F]{64})[ \t]+[*]?([^\r\n]+)$")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_checksum(path: Path, expected_name: str) -> str:
    lines = [line.strip() for line in path.read_text(encoding="ascii").splitlines() if line.strip()]
    if len(lines) != 1:
        raise ValueError(f"{path} must contain exactly one checksum line")
    match = CHECKSUM_RE.fullmatch(lines[0])
    if match is None:
        raise ValueError(f"{path} is not a valid SHA-256 checksum file")
    checksum, filename = match.groups()
    if filename != expected_name:
        raise ValueError(
            f"{path} names {filename!r}, expected the canonical asset {expected_name!r}"
        )
    return checksum.lower()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("jar", type=Path)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", type=Path, metavar="CHECKSUM_FILE")
    mode.add_argument("--verify", type=Path, metavar="CHECKSUM_FILE")
    args = parser.parse_args()

    jar = args.jar.resolve(strict=True)
    if not jar.is_file():
        raise ValueError(f"Runner artifact is not a regular file: {jar}")
    actual = sha256(jar)

    if args.write is not None:
        args.write.write_text(f"{actual}  {jar.name}\n", encoding="ascii")
    else:
        expected = read_checksum(args.verify, jar.name)
        if actual != expected:
            raise ValueError(
                f"SHA-256 mismatch for {jar.name}: expected {expected}, got {actual}"
            )

    print(actual)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
