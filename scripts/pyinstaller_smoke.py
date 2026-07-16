#!/usr/bin/env python3
"""Decode a bundled fixture from an actual PyInstaller-frozen executable."""

from __future__ import annotations

import sys
from pathlib import Path

from pyzxing import BarCodeReader


def main() -> int:
    bundle_root_value = getattr(sys, "_MEIPASS", None)
    if bundle_root_value is None:
        raise RuntimeError("this smoke harness must run as a PyInstaller-frozen executable")

    bundle_root = Path(bundle_root_value)
    jars = list((bundle_root / "runner").glob("*.jar"))
    if len(jars) != 1:
        raise RuntimeError(f"expected exactly one bundled Runner JAR, found {jars!r}")
    fixture = bundle_root / "fixtures" / "qrcode.png"
    if not fixture.is_file():
        raise RuntimeError(f"bundled decode fixture is missing: {fixture}")

    results = BarCodeReader(jar_path=jars[0]).decode(fixture)
    if not any(result.get("text") or result.get("raw") for result in results):
        raise RuntimeError(f"frozen decode returned no barcode payload: {results!r}")
    print(f"frozen decode passed with {jars[0].name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
