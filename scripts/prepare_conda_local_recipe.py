#!/usr/bin/env python3
"""Create a temporary conda recipe backed by an already-verified local JAR."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path

from verify_version_sync import ROOT, read_conda_variables, read_python_constants


SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def replace_once(text: str, old: str, new: str) -> str:
    if text.count(old) != 1:
        raise ValueError(f"temporary recipe expected exactly one source line: {old}")
    return text.replace(old, new, 1)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--jar", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--recipe", default=ROOT / "conda-recipe", type=Path)
    args = parser.parse_args()

    jar = args.jar.resolve(strict=True)
    recipe = args.recipe.resolve(strict=True)
    output = args.output.resolve()
    if not recipe.is_dir():
        raise ValueError(f"conda recipe is not a directory: {recipe}")
    if output.exists():
        raise ValueError(f"temporary recipe output already exists: {output}")

    config = read_python_constants(ROOT / "pyzxing" / "config.py", "Config")
    variables = read_conda_variables(recipe / "meta.yaml")
    if jar.name != config["JAR_FILENAME"] or jar.name != variables.get("runner_filename"):
        raise ValueError("local Runner filename differs from Config or the committed conda recipe")
    expected_sha = config["JAR_SHA256"]
    if SHA256_RE.fullmatch(expected_sha) is None or expected_sha == "0" * 64:
        raise ValueError("Config.JAR_SHA256 must be finalized before the conda publication gate")
    if variables.get("runner_sha256") != expected_sha:
        raise ValueError("committed conda Runner SHA-256 differs from Config")
    if sha256(jar) != expected_sha:
        raise ValueError("local canonical Runner SHA-256 differs from Config")
    source_commit = config["RUNNER_SOURCE_COMMIT"]
    if COMMIT_RE.fullmatch(source_commit) is None:
        raise ValueError("Config.RUNNER_SOURCE_COMMIT must be finalized before the conda gate")
    if variables.get("runner_source_commit") != source_commit:
        raise ValueError("committed conda Runner source commit differs from Config")

    shutil.copytree(recipe, output)
    temporary_meta = output / "meta.yaml"
    text = temporary_meta.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "  - path: ..",
        f"  - path: {json.dumps(str(ROOT))}",
    )
    text = replace_once(
        text,
        "  - url: https://github.com/ChenjieXu/pyzxing/releases/download/"
        "v{{ runner_version }}/{{ runner_filename }}",
        f"  - url: {json.dumps(jar.as_uri())}",
    )
    temporary_meta.write_text(text, encoding="utf-8")

    # The temporary source still carries the committed filename and checksum,
    # so conda-build independently verifies the exact bytes fetched via file://.
    if "fn: {{ runner_filename }}" not in text or "sha256: {{ runner_sha256 }}" not in text:
        raise ValueError("temporary recipe lost the canonical filename or checksum gate")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
